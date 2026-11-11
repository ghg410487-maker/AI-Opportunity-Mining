import time, requests
from .base import BaseCollector

class V2EXCollector(BaseCollector):
    source_name = "V2EX"

    def fetch(self, query, limit=30):
        out = []
        headers = {"User-Agent": "Mozilla/5.0 (compatible; DataMiningBot/1.0)"}
        # 抓取多个热门节点的最新和热门帖子
        urls = [
            "https://www.v2ex.com/api/topics/latest.json",
            "https://www.v2ex.com/api/topics/hot.json"
        ]
        
        all_items = []
        for u in urls:
            try:
                r = requests.get(u, headers=headers, timeout=20)
                if r.status_code == 200:
                    all_items.extend(r.json())
            except Exception as e:
                print(f"[V2EX] request error: {e}")
                
        keywords = query.split()
        for it in all_items:
            if len(out) >= limit:
                break
            title = it.get("title", "")
            content = it.get("content", "")
            text = title + content
            
            # 只要包含搜索词的帖子
            if any(k in text for k in keywords):
                out.append({
                    "title": title,
                    "content": content,
                    "url": it.get("url", ""),
                    "published_at": time.strftime('%Y-%m-%d', time.localtime(it.get("created", 0))),
                    "heat": {"views": None, "discussion": it.get("replies", 0), "collects": None, "stars": None, "shares": None}
                })
        return out[:limit]