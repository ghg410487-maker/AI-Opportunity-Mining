import time, requests
from .base import BaseCollector

class JuejinCollector(BaseCollector):
    source_name = "掘金"
    API = "https://api.juejin.cn/search_api/v1/search"

    def fetch(self, query, limit=30):
        out = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }
        
        try:
            # 必须强制 int(limit)，否则接口会报 str 错误
            r = requests.post(self.API, json={"key_word": query, "id_type": 0, "limit": int(limit), "search_type": 0}, headers=headers, timeout=20)
            data = r.json()
            
            if data.get("err_no") != 0:
                print(f"[Juejin] API error: {data.get('err_msg')}")
                return out
                
            items = data.get("data", [])
            for it in items:
                item_info = it.get("result_model", {}).get("article_info", {})
                if not item_info:
                    continue
                
                # 处理可能缺失的字段
                ctime = item_info.get("ctime", "0")
                try:
                    # 掘金的时间戳通常是字符串，转成 int 再转时间
                    ctime_int = int(ctime)
                    pub_date = time.strftime('%Y-%m-%d', time.localtime(ctime_int))
                except:
                    pub_date = ""

                out.append({
                    "title": item_info.get("title", ""),
                    "content": item_info.get("brief_content", ""),
                    "url": f"https://juejin.cn/post/{item_info.get('article_id', '')}",
                    "published_at": pub_date,
                    "heat": {
                        "views": item_info.get("view_count", 0), 
                        "discussion": item_info.get("comment_count", 0), 
                        "collects": item_info.get("collect_count", 0), 
                        "stars": None, 
                        "shares": None
                    }
                })
        except Exception as e:
            print(f"[Juejin] error: {e}")
            
        return out[:limit]