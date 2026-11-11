import requests
from .base import BaseCollector

class HuggingFaceCollector(BaseCollector):
    source_name = "Hugging Face"
    API = "https://huggingface.co/api/models"

    def fetch(self, query, limit=30):
        out = []
        try:
            # 按下载量排序（热点）
            r = requests.get(self.API, params={
                "search": query, "limit": limit, "sort": "downloads", "direction": -1
            }, timeout=20)
            
            if r.status_code == 200:
                for it in r.json():
                    model_id = it.get("modelId", "")
                    last_modified = it.get("lastModified", "")
                    # 时间过滤，排除 2021 年前死的项目
                    if last_modified and last_modified[:4].isdigit() and int(last_modified[:4]) < 2021:
                        continue
                        
                    out.append({
                        "title": model_id,
                        "content": f"Tags: {', '.join(it.get('tags', []))}. Pipeline: {it.get('pipeline_tag', 'N/A')}",
                        "url": f"https://huggingface.co/{model_id}",
                        "published_at": last_modified[:10],
                        "heat": {"stars": it.get("likes", 0), "discussion": None, "views": None, "collects": it.get("downloads", 0), "shares": None}
                    })
        except Exception as e:
            print(f"[HuggingFace] error: {e}")
        return out[:limit]