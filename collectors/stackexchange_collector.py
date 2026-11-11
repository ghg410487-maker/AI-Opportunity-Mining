import time, requests
from .base import BaseCollector

class StackExchangeCollector(BaseCollector):
    source_name = "Stack Exchange"
    API = "https://api.stackexchange.com/2.3/search/advanced"

    def fetch(self, query, limit=30):
        out = []
        try:
            # 近五年（1672531200 是 2023-01-01，这里设置从 2021 开始）
            r = requests.get(self.API, params={
                "order": "desc", "sort": "relevance", "q": query,
                "site": "stackoverflow", "pagesize": limit,
                "fromdate": 1609459200 # 2021-01-01 的时间戳
            }, timeout=20)
            
            if r.status_code == 200:
                for it in r.json().get("items", []):
                    out.append({
                        "title": it.get("title", ""),
                        "content": "", 
                        "url": it.get("link", ""),
                        "published_at": time.strftime('%Y-%m-%d', time.localtime(it.get("creation_date", 0))),
                        "heat": {"views": it.get("view_count", 0), "discussion": it.get("answer_count", 0), "stars": it.get("score", 0), "collects": None, "shares": None}
                    })
        except Exception as e:
            print(f"[StackExchange] error: {e}")
        return out[:limit]