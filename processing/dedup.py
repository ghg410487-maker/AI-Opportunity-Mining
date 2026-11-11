import hashlib


def dedup_exact(records):
    """URL 精确去重 + content_hash 精确去重，保留第一条。"""
    kept, removed = [], []
    seen_url, seen_hash = {}, {}
    for r in records:
        url = (r.get("source_url") or "").strip().lower().rstrip("/")
        h = r.get("content_hash") or hashlib.sha256(
            ((r.get("source_url") or "") + "\n" + (r.get("content") or "")).encode("utf-8")
        ).hexdigest()
        r["content_hash"] = h
        if url and url in seen_url:
            removed.append({"record_id": r["record_id"],
                            "reason": "duplicate_url", "kept_id": seen_url[url]})
            continue
        if h in seen_hash:
            removed.append({"record_id": r["record_id"],
                            "reason": "duplicate_content", "kept_id": seen_hash[h]})
            continue
        kept.append(r)
        if url:
            seen_url[url] = r["record_id"]
        seen_hash[h] = r["record_id"]
    return kept, removed