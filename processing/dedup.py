import hashlib
import re

def normalize_text(text):
    """简单文本规范化，去掉所有空格和标点，用于比对正文"""
    if not text:
        return ""
    return re.sub(r'\s+', '', re.sub(r'[^\w]', '', text)).lower()

def dedup_exact(records):
    """
    精确去重：
    1) 相同 URL 去重
    2) 相同 content_hash (整段文本) 去重
    3) 不同 URL 但正文完全一致 去重（曹的要求）
    """
    kept, removed = [], []
    seen_url = {}
    seen_content_norm = {}
    
    for r in records:
        url = (r.get("source_url") or "").strip().lower().rstrip("/")
        content = r.get("content", "")
        
        # 生成正文规范化指纹
        norm_content = normalize_text(content)
        if not norm_content:
            # 如果正文为空，用标题兜底
            norm_content = normalize_text(r.get("title", ""))
            
        h = hashlib.sha256(norm_content.encode("utf-8")).hexdigest()
        
        # 1. 判断 URL 重复
        if url and url in seen_url:
            removed.append({"record_id": r["record_id"], "reason": "duplicate_url", "kept_id": seen_url[url]})
            continue
            
        # 2. 判断正文内容重复（忽略来源 URL）
        if norm_content and h in seen_content_norm:
            removed.append({"record_id": r["record_id"], "reason": "duplicate_content_diff_url", "kept_id": seen_content_norm[h]})
            continue
            
        # 保留该记录
        kept.append(r)
        if url:
            seen_url[url] = r["record_id"]
        if norm_content:
            seen_content_norm[h] = r["record_id"]
            
    return kept, removed