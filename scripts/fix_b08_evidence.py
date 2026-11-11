import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from processing.clean import clean_record
from processing.dedup import dedup_exact
from processing.export_result1 import export
from collectors.base import dump_jsonl

# 曹要求：为了不覆盖旧的127条版本，新版命名为 B08_new
BATCH = "B08_new"
raw_path = f"data/raw/{BATCH}/records.jsonl"

if not os.path.exists(raw_path):
    print(f"找不到 {raw_path}，请确认本地文件是否存在")
    sys.exit(1)

with open(raw_path, encoding="utf-8") as f:
    raw_records = [json.loads(line) for line in f if line.strip()]

print(f"读取到 {len(raw_records)} 条原始记录")

# 1. 清洗并过滤残次品
valid_records = []
dropped_count = 0
for r in raw_records:
    c = clean_record(r)
    
    # 过滤规则 1：正文为空（或者只有一两个字），直接丢弃
    if len(c.get("content", "")) < 5:
        dropped_count += 1
        continue
        
    # 过滤规则 2：B站链接没有 BV 号，直接丢弃
    if c["source_name"] == "哔哩哔哩" and "BV" not in c["source_url"]:
        dropped_count += 1
        continue
        
    valid_records.append(c)

print(f"过滤掉 {dropped_count} 条无效数据，剩余 {len(valid_records)} 条有效数据")

# 保存清洗后的有效数据（供核对）
os.makedirs(f"data/cleaned/{BATCH}", exist_ok=True)
dump_jsonl(valid_records, f"data/cleaned/{BATCH}/cleaned.jsonl")

# 2. 去重
kept, removed = dedup_exact(valid_records)
dump_jsonl(kept, f"data/cleaned/{BATCH}/deduped.jsonl")

# 3. 把去重明细单独存成一个可读的 CSV，方便曹直接看
pd.DataFrame(removed).to_csv(f"data/cleaned/{BATCH}/removed_detail.csv", index=False, encoding="utf-8-sig")
print(f"去重：保留 {len(kept)}，删除了 {len(removed)} 条")

# 4. 重新导出（这会自动生成 Markdown 快照）
export(kept, BATCH, out_path=f"results/{BATCH}/result1.csv")
print("导出完成！快照已生成在 data/snapshots 里。")