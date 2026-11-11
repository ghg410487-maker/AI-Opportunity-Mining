import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

INPUT_PATH = "data/cleaned/Combined_v1.jsonl"
OUTPUT_PATH = "data/cleaned/Combined_cleaned.jsonl"

# 极其严格的教育相关性词库
EDU_KEYWORDS = [
    "教育", "教学", "学生", "老师", "教师", "课程", "考试", "辅导", "作业", "学校", "科研", "论文", "实验", 
    "education", "learning", "student", "teacher", "tutor", "academic"
]

# 极其严格的广告与垃圾黑名单
BLACKLIST = [
    "抽奖", "直播间", "买了个", "小米", "报名啦", "训练营", "买课", "下单", "价格", 
    "招聘", "求职", "内推", "红包", "优惠券", "福利", "限时", "特价", "只要", "包过", 
    "点击购买", "加微信", "扫码", "代理", "加盟", "拼团"
]

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

records = load_jsonl(INPUT_PATH)
print(f"原始合并数据: {len(records)} 条")

cleaned_records = []
dropped_blacklist = 0
dropped_irrelevant = 0
dropped_short = 0

for r in records:
    text = (r.get("title", "") + " " + r.get("content", "")).lower()
    
    # 1. 严杀黑名单
    if any(bl in text for bl in BLACKLIST):
        dropped_blacklist += 1
        continue
        
    # 2. 严杀非教育内容
    if not any(kw in text for kw in EDU_KEYWORDS):
        dropped_irrelevant += 1
        continue
        
    # 3. 正文太短（少于 15 个字）的也砍掉
    if len(r.get("content", "")) < 15 and len(r.get("title", "")) < 10:
        dropped_short += 1
        continue
        
    cleaned_records.append(r)

print(f"清洗漏斗:")
print(f" - 黑名单广告/招聘剔除: {dropped_blacklist} 条")
print(f" - 无教育特征剔除: {dropped_irrelevant} 条")
print(f" - 内容过短剔除: {dropped_short} 条")
print(f"最终留存: {len(cleaned_records)} 条")

# 保存提纯后的数据
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for r in cleaned_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"保存至: {OUTPUT_PATH}")

# 打印一下各来源的分布
print("\n各来源留存分布:")
sources = Counter([r["source_name"] for r in cleaned_records])
for src, count in sources.most_common():
    print(f" - {src}: {count} 条")