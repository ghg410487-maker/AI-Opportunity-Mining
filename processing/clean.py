import re

URL_RE = re.compile(r"https?://\S+")
WS_RE = re.compile(r"[ \t\u3000]+")
MULTI_NL = re.compile(r"\n{3,}")
HTML_TAG_RE = re.compile(r"<[^>]+>")

def clean_text(text: str) -> str:
    if not text:
        return ""
    t = str(text)
    t = HTML_TAG_RE.sub(" ", t) # 强制剥离 HTML 标签
    t = URL_RE.sub(" ", t)
    t = WS_RE.sub(" ", t)
    t = t.replace("。 。", "。").replace("， ，", "，")
    t = MULTI_NL.sub("\n\n", t)
    return t.strip()


def clean_record(rec: dict) -> dict:
    r = dict(rec)
    r["_raw_content"] = rec.get("content", "")
    r["_raw_title"] = rec.get("title", "")
    r["content"] = clean_text(rec.get("content", ""))
    r["title"] = clean_text(rec.get("title", ""))

    for k in ["source_url", "source_name", "published_at"]:
        if r.get(k) is None:
            r[k] = ""

    return r


def is_recent(rec: dict, start_year: int = 2021) -> bool:
    """严格的时间过滤"""
    pub_time = str(rec.get("published_at", ""))
    
    # 1. 过滤没有时间的空数据
    if not pub_time.strip():
        return False
        
    # 2. 过滤英文旧时间（比如 Google News 抓到的 Tue, 28 Aug 2018...）
    # 只要包含 201 或 2020，直接毙掉
    if " 201" in pub_time or " 2020" in pub_time:
        return False
        
    # 3. 标准 YYYY-MM-DD 格式过滤
    if len(pub_time) >= 4 and pub_time[:4].isdigit():
        if int(pub_time[:4]) < start_year:
            return False
            
    return True