import os
import glob
import json

def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

# 1. 统计第一阶段（B10-B14）
b10_14_raw = 0
b10_14_clean = 0
b10_14_batches = ["B10", "B11", "B12", "B13", "B14"]
for b in b10_14_batches:
    b10_14_raw += count_lines(f"data/raw/{b}/records.jsonl")
    b10_14_clean += count_lines(f"data/cleaned/{b}/deduped.jsonl")

# 2. 统计第二阶段（SUPER 批次）
super_raw = 0
super_clean = 0
super_dirs = glob.glob("data/raw/SUPER_part*")
for d in super_dirs:
    b = os.path.basename(d)
    super_raw += count_lines(f"data/raw/{b}/records.jsonl")
    super_clean += count_lines(f"data/cleaned/{b}/deduped.jsonl")

# 3. 最终合并表
final_csv_rows = count_lines("results/final/result1_862条_最终定稿.csv") - 1 # 减去表头

print("================ 真实数据大盘点 ================")
print(f"【第一阶段 B10-B14】")
print(f"  原始抓取量: {b10_14_raw} 条")
print(f"  单批清洗量: {b10_14_clean} 条")

print(f"\n【第二阶段 SUPER 扩展批次】")
print(f"  原始抓取量: {super_raw} 条")
print(f"  单批清洗量: {super_clean} 条")

print(f"\n【全局总数据池】")
print(f"  系统累计原始抓取总量: {b10_14_raw + super_raw} 条")
print(f"  单批清洗初步留存总量: {b10_14_clean + super_clean} 条")

print(f"\n【终极跨批次合并去重后】")
print(f"  最终交付的表格数据量: {final_csv_rows} 条")
print("================================================")