import pandas as pd
import requests
import hashlib
import os
from bs4 import BeautifulSoup
import time

OUT_DIR = "docs/research_stage3/stage3d2"
os.makedirs(f"{OUT_DIR}/snapshots", exist_ok=True)

targets = [
    {"id": "SUPER_part12-S00029", "url": "https://www.bilibili.com/video/BV1inWj6TE6E"},
    {"id": "SUPER_part15-S00249", "url": "https://www.bilibili.com/video/BV1ZEWj6qEtM"},
    {"id": "SUPER_part20-S00084", "url": "https://juejin.cn/post/7419887372462686249"}
]

results = []
print("正在尝试补取3条待核原文...")

for t in targets:
    rid = t["id"]
    url = t["url"]
    status = "UNAVAILABLE"
    evidence = ""
    file_path = ""
    sha256 = ""
    
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # 简单提取页面文本
            text = soup.get_text(separator=' ', strip=True)
            evidence = text[:500] # 截取前500字作为证据
            
            # 如果抓到了内容，标记为成功
            if len(evidence) > 50:
                status = "SUCCESS"
                file_name = f"{rid}.txt"
                file_path = f"{OUT_DIR}/snapshots/{file_name}"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(evidence)
                sha256 = hashlib.sha256(evidence.encode("utf-8")).hexdigest()
    except Exception as e:
        status = "UNAVAILABLE"
        
    results.append({
        "record_id": rid,
        "source_url": url,
        "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "retrieval_status": status,
        "evidence_snippet": evidence,
        "snapshot_path": file_path,
        "snapshot_sha256": sha256
    })
    print(f"[{rid}] -> {status}")

# 保存报告
df = pd.DataFrame(results)
df.to_csv(f"{OUT_DIR}/source_retrieval_3cases.csv", index=False, encoding="utf-8-sig")

with open(f"{OUT_DIR}/source_retrieval_report.md", "w", encoding="utf-8") as f:
    f.write("# 3条待裁决记录原文补取报告\n\n")
    for r in results:
        f.write(f"## {r['record_id']}\n")
        f.write(f"- **获取状态**：{r['retrieval_status']}\n")
        f.write(f"- **获取时间**：{r['retrieved_at']}\n")
        if r['retrieval_status'] == "SUCCESS":
            f.write(f"- **证据片段**：{r['evidence_snippet']}...\n")
            f.write(f"- **快照哈希**：{r['snapshot_sha256']}\n")
        f.write("\n")

print(f"✅ 原文补取完毕，结果已存至 {OUT_DIR}")