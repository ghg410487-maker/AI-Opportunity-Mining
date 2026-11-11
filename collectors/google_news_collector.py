import time, requests, re, html
from .base import BaseCollector

class GoogleNewsCollector(BaseCollector):
    source_name = "教育官方新闻"
    API = "https://news.google.com/rss/search"

    def fetch(self, query, limit=30):
        out = []
        # 强制限定只搜 moe.gov.cn (教育部) 和 edu.cn (高校)
        q = f"{query} (site:moe.gov.cn OR site:edu.cn)"
        try:
            r = requests.get(self.API, params={"q": q, "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}, timeout=20)
            if r.status_code == 200:
                items = re.findall(r"<item>(.*?)</item>", r.text, re.S)
                for it in items[:limit]:
                    def _g(tag):
                        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", it, re.S)
                        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
                    
                    out.append({
                        "title": _g("title"),
                        "content": _g("description"),
                        "url": _g("link"),
                        "published_at": _g("pubDate"), # 已经是近期新闻
                        "heat": {"stars": None, "views": None, "discussion": None, "collects": None, "shares": None}
                    })
        except Exception as e:
            print(f"[GoogleNews] error: {e}")
        return out[:limit]