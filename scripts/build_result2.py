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
deduped_path = f"data/cleaned/{BATCH}/deduped.jsonl"

with open(deduped_path, encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

results = []
audit_logs = []  # 用于记录曹要求的具体状态
total_prompt_tokens = 0
total_completion_tokens = 0
cached_count = 0

print(f"开始处理 {len(records)} 条数据 (带深度审计规则)...")
start_time = time.time()

for i, r in enumerate(records):
    is_op, conf, func, ind, audit_status, usage = llm_judge(r)
    
    if usage.get("is_cached"):
        cached_count += 1
    else:
        total_prompt_tokens += usage.get("prompt_tokens", 0)
        total_completion_tokens += usage.get("completion_tokens", 0)
    
    # 官方要求的 CSV 数据
    results.append({
        "采集批次号": r["batch_id"],
        "记录编号": r["record_id"],
        "是否构成机会": is_op,
        "机会置信度": conf,
        "功能类别": func,
        "所属行业": ind
    })
    
    # 用于曹审核的内部审计日志
    audit_logs.append({
        "record_id": r["record_id"],
        "source": r["source_name"],
        "title": r.get("title", "")[:30],
        "is_opportunity": is_op,
        "audit_status": audit_status
    })
    
    print(f"进度: {i+1}/{len(records)} | {r['record_id']} -> 状态: {audit_status}")
    time.sleep(0.5) 

# 1. 导出官方 result2.csv
df = pd.DataFrame(results).reindex(columns=RESULT2)
os.makedirs(f"results/{BATCH}", exist_ok=True)
out_path = f"results/{BATCH}/result2.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")

# 2. 导出内部审计明细（给曹看的）
os.makedirs(f"data/audit_{BATCH}", exist_ok=True)
audit_path = f"data/audit_{BATCH}/task2_audit_detail.jsonl"
with open(audit_path, "w", encoding="utf-8") as f:
    for log in audit_logs:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

# 3. 计算成本
cost_rmb = (total_prompt_tokens / 1000000 * 1) + (total_completion_tokens / 1000000 * 2)
elapsed_time = time.time() - start_time

# 4. 生成详细成本报告
report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)
report_path = f"{report_dir}/api_cost_report_{BATCH}.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# {BATCH} 任务二 API 成本与资源报告\n\n")
    f.write(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"- **处理记录数**: {len(records)} 条\n")
    f.write(f"- **命中前置黑名单缓存(免 Token)**: {cached_count} 条\n")
    f.write(f"- **API 真实调用数**: {len(records) - cached_count} 次\n")
    f.write(f"- **输入 Token**: {total_prompt_tokens}\n")
    f.write(f"- **输出 Token**: {total_completion_tokens}\n")
    f.write(f"- **总 Token**: {total_prompt_tokens + total_completion_tokens}\n")
    f.write(f"- **预估成本**: 约 {cost_rmb:.5f} 元人民币\n")
    f.write(f"- **总耗时**: {elapsed_time:.2f} 秒\n")

print(f"\n[result2] 成功生成官方表格 {len(df)} 行 -> {out_path}")
print(f"[audit] 审计明细已保存 -> {audit_path}")
print(f"[cost] 真实调用 {len(records) - cached_count} 次，消耗 {total_prompt_tokens + total_completion_tokens} Tokens，成本约 {cost_rmb:.5f} 元")