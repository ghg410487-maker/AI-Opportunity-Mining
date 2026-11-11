import json
import os
from collections import Counter

# 读取最新批次
BATCH = "B10"
path = f"data/cleaned/{BATCH}/deduped.jsonl"

if not os.path.exists(path):
    print(f"找不到文件: {path}")
    exit()

with open(path, encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

# 1. 统计各平台数量
counts = Counter([r['source_name'] for r in records])
print("=== 各平台最终保留数量 ===")
for src, count in counts.items():
    print(f"{src}: {count} 条")

# 2. 打印各平台的 2 条样本
print("\n=== 各平台抽样展示 ===")
seen = set()
for r in records:
    src = r['source_name']
    if src not in seen:
        seen.add(src)
        print(f"\n【平台】: {src}")
        print(f"【时间】: {r.get('published_at')}")
        print(f"【标题】: {r.get('title')}")
        print(f"【内容】: {r.get('content', '')[:100]}...")