import os
import json
import hashlib
import zipfile
import pandas as pd
from datetime import datetime
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BATCH = "B10"

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    audit_dir = f"data/audit_{BATCH}"
    os.makedirs(audit_dir, exist_ok=True)
    
    raw_path = f"data/raw/{BATCH}/records.jsonl"
    cleaned_path = f"data/cleaned/{BATCH}/cleaned.jsonl"
    
    if not os.path.exists(raw_path) or not os.path.exists(cleaned_path):
        print("找不到原始或清洗数据，请确认是否跑通了 build_result1.py")
        return

    with open(raw_path, encoding="utf-8") as f:
        raw_records = [json.loads(line) for line in f if line.strip()]
    with open(cleaned_path, encoding="utf-8") as f:
        cleaned_records = [json.loads(line) for line in f if line.strip()]

    # 计算过滤和去重明细
    kept_ids = set([r["record_id"] for r in cleaned_records])
    raw_ids = set([r["record_id"] for r in raw_records])
    filtered_records = [r for r in raw_records if r["record_id"] not in raw_ids.intersection(kept_ids)]
    
    removed_df = pd.read_csv(f"data/cleaned/{BATCH}/removed_detail.csv") if os.path.exists(f"data/cleaned/{BATCH}/removed_detail.csv") else pd.DataFrame()
    dedup_records = removed_df.to_dict("records") if not removed_df.empty else []

    # 生成审计报告
    report_path = f"{audit_dir}/audit_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# {BATCH} 批次数据审计报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 1. 数据统计\n")
        f.write(f"- 原始记录: {len(raw_records)} 条\n")
        f.write(f"- 清洗后有效记录: {len(cleaned_records)} 条\n")
        f.write(f"- 被过滤记录: {len(filtered_records)} 条 (原因: 超时、黑名单、无教育特征)\n")
        f.write(f"- 被去重记录: {len(dedup_records)} 条\n")
        f.write(f"- **最终保留: {len(cleaned_records) - len(dedup_records)} 条**\n\n")

    # 整理打包文件
    files_to_pack = []
    files_to_pack.append((raw_path, f"{BATCH}/raw_records.jsonl"))
    files_to_pack.append((cleaned_path, f"{BATCH}/cleaned_records.jsonl"))
    files_to_pack.append((f"results/{BATCH}/result1.csv", f"{BATCH}/result1.csv"))
    
    # 打包快照
    snapshot_dir = "data/snapshots"
    if os.path.exists(snapshot_dir):
        for fname in os.listdir(snapshot_dir):
            if fname.startswith(BATCH.replace("_new", "")): 
                files_to_pack.append((os.path.join(snapshot_dir, fname), f"{BATCH}/snapshots/{fname}"))

    # 计算哈希并生成 Manifest
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

    # 打压缩包
    zip_path = f"{BATCH}_Audit_Package_{datetime.now().strftime('%Y%m%d')}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for local_path, arc_name in files_to_pack:
            if os.path.exists(local_path):
                zipf.write(local_path, arcname=arc_name)
                
    print(f"审计包生成成功: {zip_path}")
    print(f"包含 {len(files_to_pack)} 个文件。")

if __name__ == "__main__":
    main()