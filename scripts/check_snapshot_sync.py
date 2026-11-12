import pandas as pd
import os

# 最终表格路径
CSV_PATH = "results/final/result1_862条_最终定稿.csv" 
SNAPSHOT_DIR = "data/snapshots"

def check():
    if not os.path.exists(CSV_PATH):
        print(f"找不到最终表格 {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    final_ids = df["记录编号"].tolist()
    
    missing_snapshots = []
    valid_count = 0
    
    for rid in final_ids:
        # 快照命名规则是 B10-S00001 -> B10_S00001.md
        snap_name = str(rid).replace("-", "_") + ".md"
        snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
        
        if not os.path.exists(snap_path):
            missing_snapshots.append(rid)
        else:
            valid_count += 1
            
    print(f"=== 快照核验报告 ===")
    print(f"最终表格记录数: {len(final_ids)} 条")
    print(f"成功找到对应的 Markdown 快照: {valid_count} 条")
    print(f"快照缺失: {len(missing_snapshots)} 条")
    
    if missing_snapshots:
        print(f"缺失记录编号 (前 10 个): {missing_snapshots[:10]}")
        with open("reports/snapshot_missing_report.md", "w", encoding="utf-8") as f:
            f.write("# 快照缺失审计报告\n\n")
            for m in missing_snapshots:
                f.write(f"- {m}\n")
    else:
        print("✅ 完美！所有最终记录的 Markdown 快照均已生成并可追溯。")

if __name__ == "__main__":
    check()