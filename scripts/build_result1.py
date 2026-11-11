import argparse, json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collectors.github_collector import GitHubCollector
from collectors.bilibili_collector import BilibiliCollector
from collectors.v2ex_collector import V2EXCollector
from collectors.juejin_collector import JuejinCollector
from collectors.base import dump_jsonl
from processing.clean import clean_record
from processing.dedup import dedup_exact
from processing.export_result1 import export

# 删除了经常报 429 的 Semantic，换上了稳定的掘金和 B站
COLLECTORS = {
    "github": GitHubCollector(),
    "bilibili": BilibiliCollector(),
    "v2ex": V2EXCollector(),
    "juejin": JuejinCollector(),
}

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--scenario", default="education_ai")
    ap.add_argument("--reuse", action="store_true")
    args = ap.parse_args()

    raw_path = f"data/raw/{args.batch}/records.jsonl"

    if args.reuse and os.path.exists(raw_path):
        print(f"[collect] reuse {raw_path}")
    else:
        seq, all_recs = 1, []
        for name, c in COLLECTORS.items():
            raw = c.fetch(args.query, args.limit)
            for x in raw:
                all_recs.append(c.to_record(x, args.batch, seq, args.scenario))
                seq += 1
            print(f"[{name}] fetched {len(raw)}")
        dump_jsonl(all_recs, raw_path)
        print(f"[collect] saved {len(all_recs)} -> {raw_path}")

    raw_records = load_jsonl(raw_path)
    cleaned = [clean_record(r) for r in raw_records]
    os.makedirs(f"data/cleaned/{args.batch}", exist_ok=True)
    dump_jsonl(cleaned, f"data/cleaned/{args.batch}/cleaned.jsonl")
    print(f"[clean] {len(cleaned)} records")

    kept, removed = dedup_exact(cleaned)
    dump_jsonl(kept, f"data/cleaned/{args.batch}/deduped.jsonl")
    with open(f"data/cleaned/{args.batch}/dedup_report.json", "w", encoding="utf-8") as f:
        json.dump({"raw": len(cleaned), "kept": len(kept), "removed": len(removed), "removed_detail": removed}, f, ensure_ascii=False, indent=2)
    print(f"[dedup] kept {len(kept)}, removed {len(removed)}")

    export(kept, args.batch, out_path=f"results/{args.batch}/result1.csv")

if __name__ == "__main__":
    main()