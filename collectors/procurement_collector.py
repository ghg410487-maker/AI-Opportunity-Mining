import requests, re, html
from .base import BaseCollector

class ProcurementCollector(BaseCollector):
    source_name = "采购与产品"
    def fetch(self, query, limit=30):
        out = []
        q = f"{query} (site:ccgp.gov.cn OR site:zol.com.cn OR site:elecfans.com)"
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
            print(f"[Procurement] error: {e}")
        return out