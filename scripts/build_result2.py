import json
import os
import sys
import pandas as pd
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mining.judge import llm_judge
from config.official_headers import RESULT2

BATCH = "B10"
# 注意：读取你修复后的 76 条数据
deduped_path = f"data/cleaned/{BATCH}/fixed/records_fixed.jsonl" 

if not os.path.exists(deduped_path):
    print(f"找不到 {deduped_path}，请确认文件是否存在")
    sys.exit(1)

with open(deduped_path, encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

results = []
audit_logs = []
total_prompt_tokens = 0
total_completion_tokens = 0

print(f"开始调用大模型处理 {len(records)} 条数据 (严格遵循 V0.2 标准)...")
start_time = time.time()

for i, r in enumerate(records):
    res_dict, usage = llm_judge(r)
    
    total_prompt_tokens += usage.get("prompt_tokens", 0)
    total_completion_tokens += usage.get("completion_tokens", 0)
    
    # 拿到大模型的内部判别结果
    state = res_dict.get("is_opportunity", "REVIEW")
    conf = float(res_dict.get("confidence", 0.0))
    
    # --- 核心：映射到官方 CSV 格式 ---
    # 官方只接受 0 或 1。如果是 REVIEW（待复核），官方表里填 0
    official_is_op = 1 if state == "1" else 0
    official_func = res_dict.get("function", "无") if state == "1" else "无"
    official_ind = res_dict.get("industry", "无") if state == "1" else "无"
    
    results.append({
        "采集批次号": r["batch_id"],
        "记录编号": r["record_id"],
        "是否构成机会": official_is_op,
        "机会置信度": conf,
        "功能类别": official_func,
        "所属行业": official_ind
    })
    
    # --- 核心：保存极其详细的内部审计日志 ---
    audit_logs.append({
        "record_id": r["record_id"],
        "source": r["source_name"],
        "title": r.get("title", "")[:30],
        "scenario": res_dict.get("scenario"),
        "evidence_type": res_dict.get("evidence_type"),
        "D1": res_dict.get("D1"), "D2": res_dict.get("D2"), "D3": res_dict.get("D3"),
        "D4": res_dict.get("D4"), "D5": res_dict.get("D5"), "D6": res_dict.get("D6"),
        "model_state": state,
        "reason_code": res_dict.get("reason_code")
    })
    
    print(f"进度: {i+1}/{len(records)} | {r['record_id']} -> 模型判定: {state} ({res_dict.get('reason_code')})")
    time.sleep(0.5)

# 1. 导出官方 result2.csv
df = pd.DataFrame(results).reindex(columns=RESULT2)
os.makedirs(f"results/{BATCH}", exist_ok=True)
out_path = f"results/{BATCH}/result2.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")

# 2. 导出 V0.2 内部审计日志
os.makedirs(f"data/audit_{BATCH}", exist_ok=True)
audit_path = f"data/audit_{BATCH}/task2_v02_audit_detail.jsonl"
with open(audit_path, "w", encoding="utf-8") as f:
    for log in audit_logs:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

# 3. 详细成本统计报告
cost_rmb = (total_prompt_tokens / 1000000 * 1) + (total_completion_tokens / 1000000 * 2)
elapsed_time = time.time() - start_time

report_path = f"reports/api_cost_report_{BATCH}_task2.md"
os.makedirs("reports", exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# Task 2 V0.2 标准 API 成本与调用报告\n\n")
    f.write(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"- **处理记录数**: {len(records)} 条\n")
    f.write(f"- **输入 Token**: {total_prompt_tokens}\n")
    f.write(f"- **输出 Token**: {total_completion_tokens}\n")
    f.write(f"- **总 Token**: {total_prompt_tokens + total_completion_tokens}\n")
    f.write(f"- **预估成本**: 约 {cost_rmb:.5f} 元人民币 (依据 DeepSeek 定价)\n")
    f.write(f"- **总耗时**: {elapsed_time:.2f} 秒\n")

print(f"\n[result2] 官方表格已生成 -> {out_path}")
print(f"[audit] V0.2 详单已生成 -> {audit_path}")
print(f"[cost] 成本预估 {cost_rmb:.5f} 元，详细报告已存至 {report_path}")