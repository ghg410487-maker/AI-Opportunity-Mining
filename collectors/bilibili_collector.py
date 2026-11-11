import time, requests, re, html
from .base import BaseCollector

class BilibiliCollector(BaseCollector):
    source_name = "哔哩哔哩"
    API = "https://api.bilibili.com/x/web-interface/search/type"

    def fetch(self, query, limit=30):
        out = []
        session = requests.Session()
        # 添加全套 Header 和 Cookie 伪装成浏览器
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": "buvid3=infoc; b_nut=1700000000; i-wanna-go-back=-1; b_ut=7; _uuid=xxxxx"
        })
        
        page = 1
        while len(out) < limit and page <= 5:
            try:
                r = session.get(self.API, params={
                    "search_type": "video", "keyword": query, "page": page
                }, timeout=20)
                
                # 防拦截判定
                if not r.text.strip().startswith('{'):
                    print("[Bilibili] 触发了反爬拦截，返回了 HTML 页面")
                    break
                
                data = r.json()
                if data.get("code") != 0:
                    print(f"[Bilibili] API 错误: {data.get('message')}")
                    break
                items = data.get("data", {}).get("result", [])
                if not items:
                    break
                for it in items:
                    title = html.unescape(re.sub(r'<[^>]+>', '', it.get("title", "")))
                    desc = html.unescape(re.sub(r'<[^>]+>', '', it.get("description", "")))
                    out.append({
                        "title": title,
                        "content": desc,
                        "url": f"https://www.bilibili.com/video/{it.get('bvid', '')}",
                        "published_at": time.strftime('%Y-%m-%d', time.localtime(it.get("pubdate", 0))),
                        "heat": {"views": it.get("play", 0), "discussion": it.get("review", 0), "collects": it.get("favorites", 0), "stars": None, "shares": None}
                    })
                page += 1
                time.sleep(2)
            except Exception as e:
                print(f"[Bilibili] 异常: {e}")
                break
        return out[:limit]