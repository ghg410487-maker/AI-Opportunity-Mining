import re
import datetime

URL_RE = re.compile(r"https?://\S+")
WS_RE = re.compile(r"[ \t\u3000]+")
MULTI_NL = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    if not text:
        return ""
    t = str(text)
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

    # 修复 1970 年的脏时间，置为空
    if r["published_at"].startswith("1970") or r["published_at"] == "0":
        r["published_at"] = ""

    return r