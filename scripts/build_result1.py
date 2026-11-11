import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 原有的 8 个采集器
from collectors.github_collector import GitHubCollector
from collectors.bilibili_collector import BilibiliCollector
from collectors.v2ex_collector import V2EXCollector
from collectors.juejin_collector import JuejinCollector
from collectors.openalex_collector import OpenAlexCollector
from collectors.huggingface_collector import HuggingFaceCollector
from collectors.stackexchange_collector import StackExchangeCollector
from collectors.google_news_collector import GoogleNewsCollector

# 新增的 2 个采集器（教育论坛 & 采购评价）
from collectors.edu_forum_collector import EduForumCollector
from collectors.procurement_collector import ProcurementCollector

from collectors.base import dump_jsonl
from processing.clean import clean_record, is_recent
from processing.dedup import dedup_exact
from processing.export_result1 import export

# 注册所有的 10 个采集器
COLLECTORS = {
    "github": GitHubCollector(),
    "bilibili": BilibiliCollector(),
    "v2ex": V2EXCollector(),
    "juejin": JuejinCollector(),
    "openalex": OpenAlexCollector(),
    "huggingface": HuggingFaceCollector(),
    "stackexchange": StackExchangeCollector(),
    "googlenews": GoogleNewsCollector(),
    "eduforum": EduForumCollector(),      # 新增
    "procurement": ProcurementCollector() # 新增
}

# 强关联教育词汇（必须命中至少一个）
EDU_KEYWORDS = [
    "教育", "教学", "学生", "老师", "教师", "课程", "考试", "辅导", "作业", "学校", "科研", "论文", "实验", 
    "education", "learning", "student", "teacher", "tutor", "academic"
]

# 噪音黑名单（命中任何一个直接干掉）
BLACKLIST = [
    "抽奖", "直播间", "买了个", "小米", "报名啦", "训练营", "买课", "下单", "价格", 
    "招聘", "求职", "内推", "红包", "优惠券", "抽奖", "福利"
]

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--scenario", default="education_ai")
    ap.add_argument("--reuse", action="store_true")
    args = ap.parse_args()

    raw_path = f"data/raw/{args.batch}/records.jsonl"
    query_list = [q.strip() for q in args.queries.split(",") if q.strip()]

    # ============ 1. 采集阶段 ============
    if args.reuse and os.path.exists(raw_path):
        print(f"[collect] 复用已有原始数据 {raw_path}")
    else:
        seq, all_recs = 1, []
        for query in query_list:
            print(f"========== 正在搜索主题: {query} ==========")
            for name, c in COLLECTORS.items():
                raw = c.fetch(query, args.limit)
                for x in raw:
                    all_recs.append(c.to_record(x, args.batch, seq, args.scenario))
                    seq += 1
                print(f"[{name}] fetched {len(raw)}")
        dump_jsonl(all_recs, raw_path)
        print(f"\n[collect] 共保存 {len(all_recs)} 条原始记录 -> {raw_path}")

    # ============ 2. 清洗与过滤阶段 ============
    raw_records = load_jsonl(raw_path)
    cleaned = []
    dropped_old = 0
    dropped_blacklist = 0
    dropped_irrelevant = 0
    dropped_empty = 0
    
    for r in raw_records:
        c = clean_record(r)
        
        # 规则 1：时间底线过滤（强制 >= 2021年）
        if not is_recent(c, start_year=2021):
            dropped_old += 1
            continue
            
        text = (c.get("title", "") + " " + c.get("content", "")).lower()

        # 规则 2：黑名单过滤
        if any(bl in text for bl in BLACKLIST):
            dropped_blacklist += 1
            continue

        # 规则 3：强相关教育词汇过滤
        if not any(kw in text for kw in EDU_KEYWORDS):
            dropped_irrelevant += 1
            continue

        # 规则 4：空文本过滤
        if len(c.get("content", "")) < 5 and len(c.get("title", "")) < 5:
            dropped_empty += 1
            continue
            
        cleaned.append(c)
        
    print(f"[clean] 保留 {len(cleaned)} 条。")
    print(f"        过滤明细：老旧/无时间 {dropped_old} 条，黑名单 {dropped_blacklist} 条，无教育特征 {dropped_irrelevant} 条，空文本 {dropped_empty} 条。")
    
    os.makedirs(f"data/cleaned/{args.batch}", exist_ok=True)
    dump_jsonl(cleaned, f"data/cleaned/{args.batch}/cleaned.jsonl")

    # ============ 3. 去重阶段 ============
    kept, removed = dedup_exact(cleaned)
    dump_jsonl(kept, f"data/cleaned/{args.batch}/deduped.jsonl")
    print(f"[dedup] 最终保留 {len(kept)} 条，去重删除了 {len(removed)} 条")

    # ============ 4. 导出阶段 ============
    export(kept, args.batch, out_path=f"results/{args.batch}/result1.csv")

if __name__ == "__main__":
    main()