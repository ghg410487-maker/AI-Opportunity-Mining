import os
import json
import hashlib
import zipfile
import pandas as pd
from datetime import datetime
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 按照曹的要求：保留旧版 127 条为 B08_old，新版 115 条为 B08_new
OLD_BATCH = "B08"       # 你之前跑的 127 条版本
NEW_BATCH = "B08_new"   # 我们等下用过滤规则重新生成的 115 条版本

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # 1. 确保目录存在
    audit_dir = f"data/audit_{NEW_BATCH}"
    os.makedirs(audit_dir, exist_ok=True)
    
    # 2. 读取新旧数据
    old_raw_path = f"data/raw/{OLD_BATCH}/records.jsonl"
    new_raw_path = f"data/raw/{NEW_BATCH}/records.jsonl"
    
    if not os.path.exists(old_raw_path) or not os.path.exists(new_raw_path):
        print("找不到原始数据，请确认是否运行了 fix_b08_evidence.py 并生成了 B08_new 数据。")
        return

    with open(new_raw_path, encoding="utf-8") as f:
        raw_records = [json.loads(line) for line in f if line.strip()]
        
    cleaned_path = f"data/cleaned/{NEW_BATCH}/cleaned.jsonl"
    with open(cleaned_path, encoding="utf-8") as f:
        cleaned_records = [json.loads(line) for line in f if line.strip()]

    # 3. 计算过滤和去重明细
    kept_ids = set([r["record_id"] for r in cleaned_records])
    raw_ids = set([r["record_id"] for r in raw_records])
    
    # 过滤明细
    filtered_records = [r for r in raw_records if r["record_id"] not in raw_ids.intersection(kept_ids)]
    
    # 去重明细
    removed_df = pd.read_csv(f"data/cleaned/{NEW_BATCH}/removed_detail.csv")
    dedup_records = removed_df.to_dict("records")

    # 4. 生成审计报告 (Markdown)
    report_path = f"{audit_dir}/audit_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# B08 批次数据审计报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 1. 数据统计\n")
        f.write(f"- 原始记录: {len(raw_records)} 条\n")
        f.write(f"- 清洗后有效记录: {len(cleaned_records)} 条\n")
        f.write(f"- 被过滤记录: {len(filtered_records)} 条 (原因: 正文缺失、B站BV号缺失)\n")
        f.write(f"- 被去重记录: {len(dedup_records)} 条\n")
        f.write(f"- **最终保留: {len(cleaned_records) - len(dedup_records)} 条**\n\n")
        f.write(f"## 2. 过滤明细\n")
        for r in filtered_records:
            f.write(f"- {r['record_id']}: 链接={r.get('source_url')}, 标题={r.get('title')}\n")
        f.write(f"\n## 3. 去重明细\n")
        for r in dedup_records:
            f.write(f"- 被删: {r['record_id']}, 原因: {r['reason']}, 保留: {r['kept_id']}\n")

    # 5. 整理要打包的文件清单
    files_to_pack = []
    
    # 原始数据 & 清洗数据
    files_to_pack.append((new_raw_path, f"{NEW_BATCH}/raw_records.jsonl"))
    files_to_pack.append((cleaned_path, f"{NEW_BATCH}/cleaned_records.jsonl"))
    files_to_pack.append((f"data/cleaned/{NEW_BATCH}/removed_detail.csv", f"{NEW_BATCH}/removed_detail.csv"))
    
    # 最终 result1.csv
    files_to_pack.append((f"results/{NEW_BATCH}/result1.csv", f"{NEW_BATCH}/result1.csv"))
    
    # 115 份 Markdown 快照
    snapshot_dir = "data/snapshots"
    if os.path.exists(snapshot_dir):
        for fname in os.listdir(snapshot_dir):
            if fname.startswith(NEW_BATCH.replace("_new", "")): 
                files_to_pack.append((os.path.join(snapshot_dir, fname), f"{NEW_BATCH}/snapshots/{fname}"))

    # 6. 生成 Manifest 和 SHA-256
    manifest = []
    for local_path, arc_name in files_to_pack:
        if os.path.exists(local_path):
            manifest.append({
                "file": arc_name,
                "sha256": calculate_sha256(local_path),
                "size_bytes": os.path.getsize(local_path)
            })
            
    with open(f"{audit_dir}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    files_to_pack.append((report_path, "audit_report.md"))
    files_to_pack.append((f"{audit_dir}/manifest.json", "manifest.json"))

    # 7. 打包成 ZIP
    zip_path = f"B08_Audit_Package_{datetime.now().strftime('%Y%m%d')}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for local_path, arc_name in files_to_pack:
            if os.path.exists(local_path):
                zipf.write(local_path, arcname=arc_name)
                
    print(f"审计包生成成功: {zip_path}")
    print(f"包含 {len(files_to_pack)} 个文件。")

if __name__ == "__main__":
    main()