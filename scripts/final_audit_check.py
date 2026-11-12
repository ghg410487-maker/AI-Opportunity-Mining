import os
import json
import pandas as pd

def count_lines(path):
    if not os.path.exists(path): return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

print("================ 底盘数据审计核验 ================")

# 1. 统计真正的原始文件记录数
raw_total = 0
for root, dirs, files in os.walk("data/raw"):
    if "records.jsonl" in files:
        raw_total += count_lines(os.path.join(root, "records.jsonl"))
print(f"1. 原始抓取总量 (JSONL实际行数): {raw_total} 条")

# 2. 统计单批次清洗后总量
clean_total = 0
for root, dirs, files in os.walk("data/cleaned"):
    if "deduped.jsonl" in files:
        clean_total += count_lines(os.path.join(root, "deduped.jsonl"))
print(f"2. 单批次初步清洗后总量 (JSONL实际行数): {clean_total} 条")

# 3. 终极合并表真实去重数量
csv_path = "results/final/result1_Final_All.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    unique_ids = df["记录编号"].nunique()
    print(f"3. 最终交付的 CSV 中，唯一的【记录编号】数量: {unique_ids} 条")
    print(f"   (注意：Pandas 读出来的物理总行数是 {len(df)} 行，这通常是因为正文内含有换行符导致)")
else:
    print("未找到最终交付的 CSV。")

# 4. 快照真实数量
snap_dir = "data/snapshots"
snap_files = [f for f in os.listdir(snap_dir) if f.endswith(".md")] if os.path.exists(snap_dir) else []
print(f"4. 快照文件夹中的 Markdown 文件总数: {len(snap_files)} 份")

# 5. 最终 CSV 中真实的空正文数量
if os.path.exists(csv_path):
    empty_count = 0
    for idx, row in df.iterrows():
        if len(str(row.get("内容", "")).strip()) < 10:
            empty_count += 1
    print(f"5. 最终 CSV 中，真实的空正文/过短正文数量: {empty_count} 条")
    
print("==================================================")
print("请核对上述数据。下一步将基于此生成正式审计文件。")