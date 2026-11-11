import os
import pandas as pd
from config.official_headers import RESULT1

HEAT_COL = "热度指标（如浏览数、点赞数、讨论数等）"
SNAPSHOT_DIR = "data/snapshots"


def _heat_string(heat: dict) -> str:
    if not heat:
        return ""
    mapping = [
        ("点赞数", ["stars", "likes", "like"]),
        ("评论数", ["discussion", "comments", "comment"]),
        ("收藏数", ["collects", "collections", "favorites"]),
        ("转发量", ["shares", "reposts", "retweets"]),
    ]
    parts, used = [], set()
    for cn, keys in mapping:
        for k in keys:
            v = heat.get(k)
            if v is not None:
                parts.append(f"{cn}:{v}")
                used.add(k)
                break
    for k, v in heat.items():
        if k not in used and v is not None:
            parts.append(f"{k}:{v}")
    return ";".join(parts)


def _save_snapshot(record) -> str:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    fname = record["record_id"].replace("-", "_") + ".md"
    path = os.path.join(SNAPSHOT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {record.get('title','')}\n\n")
        f.write(f"- 来源：{record.get('source_name','')}\n")
        f.write(f"- URL：{record.get('source_url','')}\n")
        f.write(f"- 发布时间：{record.get('published_at','')}\n")
        f.write(f"- 记录编号：{record.get('record_id','')}\n\n")
        f.write("## 清洗后正文\n\n")
        f.write(record.get("content", ""))
        f.write("\n")
    return f"data/snapshots/{fname}"


def export(records, batch_id, out_path="results/result1.csv"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rows = []
    for r in records:
        rows.append({
            "采集批次号": r["batch_id"],
            "记录编号": r["record_id"],
            "来源网站名称": r["source_name"],
            "来源链接": r["source_url"],
            "内容": _save_snapshot(r),
            "发布时间": r.get("published_at", ""),
            HEAT_COL: _heat_string(r.get("heat")),
        })
    df = pd.DataFrame(rows).reindex(columns=RESULT1)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[result1] saved {len(df)} rows -> {out_path}")
    return df