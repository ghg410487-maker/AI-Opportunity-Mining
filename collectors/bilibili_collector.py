import time, requests, re, html
from .base import BaseCollector

class BilibiliCollector(BaseCollector):
    source_name = "哔哩哔哩"
    API = "https://api.bilibili.com/x/web-interface/search/type"

    def fetch(self, query, limit=30):
        out = []
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": "buvid3=infoc; b_nut=1700000000; i-wanna-go-back=-1; b_ut=7; _uuid=xxxxx"
        })
        
        page = 1
        while len(out) < limit and page <= 8:
            # 偶数页按热度(最多播放)，奇数页按最新发布(近期热点)
            order_type = "click" if page % 2 == 0 else "pubdate"
            
            try:
                r = session.get(self.API, params={
                    "search_type": "video", 
                    "keyword": query, 
                    "page": page,
                    "order": order_type
                }, timeout=20)
                
                if not r.text.strip().startswith('{'):
                    break
                
                data = r.json()
                if data.get("code") != 0:
                    break
                items = data.get("data", {}).get("result", [])
                if not items:
                    break
                for it in items:
                    title = html.unescape(re.sub(r'<[^>]+>', '', it.get("title", "")))
                    desc = html.unescape(re.sub(r'<[^>]+>', '', it.get("description", "")))
                    pub_time = it.get("pubdate", 0)
                    pub_date = time.strftime('%Y-%m-%d', time.localtime(pub_time)) if pub_time else ""
                    
                    out.append({
                        "title": title,
                        "content": desc,
                        "url": f"https://www.bilibili.com/video/{it.get('bvid', '')}",
                        "published_at": pub_date,
                        "heat": {"views": it.get("play", 0), "discussion": it.get("review", 0), "collects": it.get("favorites", 0), "stars": None, "shares": None}
                    })
                page += 1
                time.sleep(2)
            except Exception as e:
                print(f"[Bilibili] 异常: {e}")
                break
        return out[:limit]