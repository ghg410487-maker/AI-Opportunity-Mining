import json
import os
import sys
import pandas as pd
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mining.judge import llm_judge_t0

# 读取郭哥给的 42 条数据
INPUT_PATH = "data/pilot_sample_42.csv" # 请确保这个文件放到了 data/ 目录下
if not os.path.exists(INPUT_PATH):
    print(f"找不到 {INPUT_PATH}，请先把文件放到 data/ 目录下！")
    sys.exit(1)

df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig").fillna("")
os.makedirs("reports/t0_pilot", exist_ok=True)

results = []
print(f"开始执行 T0 教育相关性自动判别，共 {len(df)} 条...")

for i, row in df.iterrows():
    rid = row["record_id"]
    content = str(row["content"])
    
    # 如果郭哥给的数据里 content 为空，直接强制返回 UNKNOWN
    if not content or content.strip() == "":
        res_dict = {"t0_label": "UNKNOWN", "evidence": "NO_VISIBLE_CONTENT", "reason": "正文为空"}
    else:
        res_dict, _ = llm_judge_t0({"record_id": rid, "content": content})
    
    # 提取郭哥的人工标签（如果在这张表里的话）
    # 从表头看，似乎 annotator_a_label 和 annotator_b_label 还是空的，但我们可以预留下来
    manual_a = row.get("annotator_a_label", "")
    manual_b = row.get("annotator_b_label", "")
    
    results.append({
        "record_id": rid,
        "machine_t0_label": res_dict.get("t0_label"),
        "machine_evidence": res_dict.get("evidence"),
        "machine_reason": res_dict.get("reason"),
        "annotator_a_label": manual_a,
        "annotator_b_label": manual_b,
        "match_a": "MATCH" if res_dict.get("t0_label") == manual_a else "DIFF",
        "match_b": "MATCH" if res_dict.get("t0_label") == manual_b else "DIFF"
    })
    
    print(f"进度: {i+1}/{len(df)} | {rid} -> 机器: {res_dict.get('t0_label')}")
    time.sleep(0.3)

# 1. 导出自动判别结果 CSV（供曹和郭核对）
out_df = pd.DataFrame(results)
out_df.to_csv("reports/t0_pilot/t0_machine_predictions_42.csv", index=False, encoding="utf-8-sig")

# 2. 生成简要测试报告
with open("reports/t0_pilot/00_t0_test_report.md", "w", encoding="utf-8") as f:
    f.write("# T0 教育相关性自动判别 Pilot 测试报告\n\n")
    f.write(f"- 样本总数：42 条\n")
    f.write(f"- 判别模型：DeepSeek-V3\n\n")
    
    # 统计机器分类分布
    counts = out_df["machine_t0_label"].value_counts()
    f.write("## 机器分类分布\n")
    for label, count in counts.items():
        f.write(f"- {label}: {count} 条\n")
        
    f.write("\n## 边界样本说明\n")
    f.write("对于空正文、无法获取原文的样本，机器严格输出 UNKNOWN，未做任何强行映射。\n")
    f.write("待郭的人工标签补充后，将自动计算一致率与 Cohen's Kappa 系数。\n")

print(f"\n✅ T0 判别完成！请查看 reports/t0_pilot/")