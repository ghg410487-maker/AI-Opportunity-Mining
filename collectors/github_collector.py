import os, time, requests
from .base import BaseCollector

class GitHubCollector(BaseCollector):
    source_name = "GitHub"
    
    def fetch(self, query, limit=30):
        out = []
        headers = {"Accept": "application/vnd.github+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # 1. 搜仓库
        try:
            r = requests.get("https://api.github.com/search/repositories", 
                             params={"q": query, "sort": "stars", "per_page": limit//2}, 
                             headers=headers, timeout=20)
            if r.status_code == 200:
                for it in r.json().get("items", []):
                    out.append({
                        "title": it.get("full_name", ""),
                        "content": (it.get("description") or ""),
                        "url": it.get("html_url", ""),
                        "published_at": (it.get("created_at") or "")[:10],
                        "heat": {"stars": it.get("stargazers_count", 0), "discussion": it.get("open_issues_count", 0), "views": None, "collects": None, "shares": None}
                    })
        except Exception as e:
            print(f"[GitHub Repo] error: {e}")

        # 2. 搜 Issues（求助、痛点）
        try:
            time.sleep(2) # 避免超频
            r = requests.get("https://api.github.com/search/issues", 
                             params={"q": f"{query} type:issue", "sort": "reactions", "per_page": limit//2}, 
                             headers=headers, timeout=20)
            if r.status_code == 200:
                for it in r.json().get("items", []):
                    out.append({
                        "title": it.get("title", ""),
                        "content": (it.get("body") or ""), # 这里藏着真实痛点
                        "url": it.get("html_url", ""),
                        "published_at": (it.get("created_at") or "")[:10],
                        "heat": {"stars": None, "discussion": it.get("comments", 0), "views": None, "collects": None, "shares": None}
                    })
        except Exception as e:
            print(f"[GitHub Issue] error: {e}")

        return out