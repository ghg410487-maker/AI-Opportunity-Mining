import requests
from .base import BaseCollector

class OpenAlexCollector(BaseCollector):
    source_name = "OpenAlex"
    API = "https://api.openalex.org/works"

    def fetch(self, query, limit=30):
        out = []
        try:
            r = requests.get(self.API, params={
                "search": query,
                "filter": "from_publication_date:2021-01-01", # 强制近五年
                "sort": "cited_by_count:desc",                # 按引用量（热点）排序
                "per-page": limit,
                "mailto": "student@example.com"
            }, timeout=20)
            
            if r.status_code == 200:
                for it in r.json().get("results", []):
                    out.append({
                        "title": it.get("title", ""),
                        "content": str(it.get("abstract_inverted_index") or ""), 
                        "url": it.get("id", ""),
                        "published_at": it.get("publication_date", ""),
                        "heat": {"stars": None, "views": None, "discussion": None, "collects": None, "shares": None, "citations": it.get("cited_by_count", 0)}
                    })
        except Exception as e:
            print(f"[OpenAlex] error: {e}")
        return out[:limit]