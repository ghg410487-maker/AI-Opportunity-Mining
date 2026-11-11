import requests, re, html
from .base import BaseCollector

class EduForumCollector(BaseCollector):
    source_name = "教育论坛"
    def fetch(self, query, limit=30):
        out = []
        q = f"{query} (site:zhihu.com OR site:csdn.net OR site:v2ex.com)"
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        try:
            r = requests.get(url, timeout=20)
            items = re.findall(r"<item>(.*?)</item>", r.text, re.S)
            for it in items[:limit]:
                def _g(tag):
                    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", it, re.S)
                    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
                out.append({
                    "title": _g("title"), "content": _g("description"), "url": _g("link"),
                    "published_at": _g("pubDate"), "heat": {"stars": None, "views": None, "discussion": None, "collects": None, "shares": None}
                })
        except Exception as e:
            print(f"[EduForum] error: {e}")
        return out