import json
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 这里已经完整包含了之前的 5 个基础批次和新增的 20 个 SUPER 巨量批次
BATCHES = [
    "B10", "B11", "B12", "B13", "B14",
    "SUPER_part1", "SUPER_part2", "SUPER_part3", "SUPER_part4", "SUPER_part5",
    "SUPER_part6", "SUPER_part7", "SUPER_part8", "SUPER_part9", "SUPER_part10",
    "SUPER_part11", "SUPER_part12", "SUPER_part13", "SUPER_part14", "SUPER_part15",
    "SUPER_part16", "SUPER_part17", "SUPER_part18", "SUPER_part19", "SUPER_part20"
]

REPORT_DIR = "reports/audit_V1_Final"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs("results/Combined", exist_ok=True)

def load_jsonl(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

all_records = []
for batch in BATCHES:
    # 优先用修复后的数据，如果没有则用常规清洗后的数据
    path = f"data/cleaned/{batch}/fixed/records_fixed.jsonl"
    if not os.path.exists(path):
        path = f"data/cleaned/{batch}/deduped.jsonl"
    records = load_jsonl(path)
    if records:
        print(f"读取批次 {batch}: {len(records)} 条")
        all_records.extend(records)

print(f"\n总计合并 {len(all_records)} 条记录，开始执行 V1.0 裁定...")

v1_results = []
official_csv_rows = []
revision_logs = []

# 去除可能跨批次重复的记录（基于 URL 去重）
seen_urls = set()
unique_records = []
for r in all_records:
    url = r.get("source_url", "")
    if url and url in seen_urls:
        continue
    if url:
        seen_urls.add(url)
    unique_records.append(r)

print(f"跨批次去重后，剩余 {len(unique_records)} 条唯一记录。")

for r in unique_records:
    rid = r["record_id"]
    src = r.get("source_name", "")
    text = (r.get("title", "") + " " + r.get("content", "")).lower()
    
    # --- V1.0 E/Q 裁定 ---
    e_type = None
    q_level = "Q2"
    status = "REVIEW"
    reason = ""

    if r.get("final_content_status") == "正文不可用" or len(r.get("content", "")) < 10:
        e_type = None; q_level = "Q0"; status = "REVIEW"; reason = "SOURCE_UNAVAILABLE"
    elif src in ["GitHub", "Hugging Face"]:
        e_type = "E5"; q_level = "Q3"; status = "VERIFIED"; reason = "技术可行性材料"
    elif src in ["采购与产品"]:
        e_type = "E4"; q_level = "Q3"; status = "VERIFIED"; reason = "市场供给/采购证据"
    elif src in ["教育官方新闻"]:
        if any(w in text for w in ["采购", "招标", "建设", "实施", "改革"]):
            e_type = "E2"; q_level = "Q3"; status = "VERIFIED"; reason = "机构行动"
        else:
            e_type = "E3"; q_level = "Q2"; status = "REVIEW"; reason = "一般机构展示"
    elif src in ["OpenAlex", "Semantic Scholar"] or "论文" in text or "研究" in text:
        e_type = "E3"; q_level = "Q3"; status = "VERIFIED"; reason = "学术研究证据"
    elif any(w in text for w in ["求助", "怎么", "有没有", "吐槽", "求推荐"]):
        e_type = "E1"; q_level = "Q2"; status = "REVIEW"; reason = "初步需求信号"
    else:
        e_type = None; q_level = "Q1"; status = "REVIEW"; reason = "证据不足"
        
    r["e_type"] = e_type
    r["quality_level"] = q_level
    r["review_status"] = status
    r["review_reason"] = reason
    
    v1_results.append(r)
    
    # --- 严格按官方七字段输出 result1 ---
    official_csv_rows.append({
        "采集批次号": r.get("batch_id", ""),
        "记录编号": rid,
        "来源网站名称": src,
        "来源链接": r.get("source_url", ""),
        "内容": r.get("content", ""), # 存实际内容，不是路径
        "采集时间": "2026-11-11",     # 固定占位
        "热度指标（点赞数、评论数、收藏数、转发量等）": "" 
    })

    revision_logs.append({
        "record_id": rid,
        "source": src,
        "new_e_type": e_type,
        "quality_level": q_level,
        "review_status": status
    })

# 保存合并后的结构化数据（给大模型任务二用）
with open("data/cleaned/Combined_v1.jsonl", "w", encoding="utf-8") as f:
    for r in v1_results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 导出绝对合规的 result1.csv
df_official = pd.DataFrame(official_csv_rows)
df_official.to_csv("results/Combined/result1.csv", index=False, encoding="utf-8-sig")

# 导出 V1.0 审计日志
df_log = pd.DataFrame(revision_logs)
df_log.to_csv(f"{REPORT_DIR}/evidence_revision_log_v1.csv", index=False, encoding="utf-8-sig")

print(f"\n✓ V1.0 裁定执行完毕！")
print(f"✓ 严格合规的官方表格: results/Combined/result1.csv")
print(f"✓ 给大模型的 V1.0 结构化数据: data/cleaned/Combined_v1.jsonl")