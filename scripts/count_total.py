import os
import json

total_raw = 0
total_clean = 0

print("=== 各批次数据盘点 ===")
for i in range(1, 9):
    batch = f"MEGA01_part{i}"
    raw_file = f"data/raw/{batch}/records.jsonl"
    clean_file = f"data/cleaned/{batch}/deduped.jsonl"
    
    if os.path.exists(raw_file):
        with open(raw_file, encoding="utf-8") as f:
            raw_count = sum(1 for _ in f if _.strip())
        
        clean_count = 0
        if os.path.exists(clean_file):
            with open(clean_file, encoding="utf-8") as f:
                clean_count = sum(1 for _ in f if _.strip())
                
        print(f"{batch}: 原始 {raw_count} 条 -> 清洗后 {clean_count} 条")
        total_raw += raw_count
        total_clean += clean_count

print("\n=== 盘点结果 ===")
print(f"MEGA 批次原始抓取总计: {total_raw} 条")
print(f"MEGA 批次清洗去重后总计: {total_clean} 条")