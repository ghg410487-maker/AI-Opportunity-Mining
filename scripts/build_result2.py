import json
import os
import sys
import pandas as pd
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mining.judge import llm_judge
from config.official_headers import RESULT2

INPUT_PATH = "results/final/result1_Final_All.csv"

if not os.path.exists(INPUT_PATH):
    print(f"找不到 {INPUT_PATH}")
    sys.exit(1)

df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig").fillna("")
results = []
audit_logs = []

total_prompt_tokens = 0
total_completion_tokens = 0
start_time = time.time()

# ================= 探路设置 =================
TEST_LIMIT = 10  # 先测试 10 条
# ============================================

print(f"开始大模型判别（测试模式，共 {TEST_LIMIT} 条）...")

for i, row in df.iterrows():
    if i >= TEST_LIMIT:
        break
        
    full_rid = str(row["记录编号"])
    batch_id = str(row.get("采集批次号", ""))
    
    if "-" in full_rid:
        short_rid = full_rid.split("-")[-1]
        if not batch_id:
            batch_id = full_rid.split("-")[0]
    else:
        short_rid = full_rid
        
    record = {
        "record_id": full_rid,
        "title": "", 
        "content": str(row["内容"])
    }
    
    res_dict, usage = llm_judge(record)
    
    total_prompt_tokens += usage.get("prompt_tokens", 0)
    total_completion_tokens += usage.get("completion_tokens", 0)
    
    state = res_dict.get("is_opportunity", "REVIEW")
    
    if state == "1":
        official_val = 1
        func_val = res_dict.get("function", "其他")
        ind_val = res_dict.get("industry", "其他")
    else:
        official_val = 0
        func_val = "" 
        ind_val = ""  
        
    results.append({
        "采集批次号": batch_id,
        "记录编号": short_rid,
        "是否构成机会": official_val,
        "机会置信度": round(float(res_dict.get("confidence", 0.0)), 2),
        "功能类别": func_val,
        "所属行业": ind_val
    })
    
    audit_logs.append({
        "record_id": full_rid,
        "model_state": state,
        "scenario": res_dict.get("scenario"),
        "evidence_type": res_dict.get("evidence_type"),
        "D1": res_dict.get("D1"), "D2": res_dict.get("D2"), "D3": res_dict.get("D3"),
        "D4": res_dict.get("D4"), "D5": res_dict.get("D5"), "D6": res_dict.get("D6"),
        "reason_code": res_dict.get("reason_code")
    })
    
    print(f"进度: {i+1}/{TEST_LIMIT} | 状态: {state} | 原因: {res_dict.get('reason_code')}")
    time.sleep(0.5)

elapsed_time = time.time() - start_time

# 保存结果
out_df = pd.DataFrame(results).reindex(columns=RESULT2)
os.makedirs("results/final", exist_ok=True)
out_df.to_csv("results/final/result2_test10.csv", index=False, encoding="utf-8-sig")

os.makedirs("reports/audit", exist_ok=True)
with open("reports/audit/task2_internal_judge_test10.jsonl", "w", encoding="utf-8") as f:
    for log in audit_logs:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

total_tokens = total_prompt_tokens + total_completion_tokens
cost_rmb = (total_prompt_tokens / 1000000 * 1.0) + (total_completion_tokens / 1000000 * 2.0)

print(f"\n✅ 测试完成！")
print(f"测试结果表: results/final/result2_test10.csv")
print(f"总消耗 Token: {total_tokens}，预估花费: 约 {cost_rmb:.5f} 元")