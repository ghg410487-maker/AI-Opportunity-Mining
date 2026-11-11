import hashlib, json, os, datetime
from typing import Iterable


class BaseCollector:
    source_name = "base"

    def fetch(self, query: str, limit: int = 30) -> Iterable[dict]:
        raise NotImplementedError

    def to_record(self, raw: dict, batch_id: str, seq: int, scenario: str) -> dict:
        content = (raw.get("content") or "").strip()
        url = (raw.get("url") or "").strip()
        content_hash = hashlib.sha256((url + "\n" + content).encode("utf-8")).hexdigest()
        return {
            "batch_id": batch_id,
            "record_id": f"{batch_id}-S{seq:05d}",
            "source_name": self.source_name,
            "source_url": url,
            "title": (raw.get("title") or "").strip(),
            "content": content,
            "published_at": raw.get("published_at") or None,
            "heat": raw.get("heat") or {},
            "scenario": scenario,
            "content_hash": content_hash,
            "collected_at": datetime.datetime.utcnow().isoformat() + "Z",
        }


def dump_jsonl(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
