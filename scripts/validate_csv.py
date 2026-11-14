import pandas as pd
import os
import sys

def validate_official_csvs():
    print("开始执行官方 CSV 校验...")
    results_dir = "results/final"
    
    # 1. result1 校验
    r1_path = f"{results_dir}/result1_Final_All.csv"
    if os.path.exists(r1_path):
        df1 = pd.read_csv(r1_path, encoding="utf-8-sig")
        assert "记录编号" in df1.columns, "result1 缺记录编号"
        assert df1["记录编号"].is_unique, "result1 记录编号有重复"
        print(f"✅ result1 校验通过 (共 {len(df1)} 条)")
    else:
        print("❌ 找不到 result1")

    # 2. result2 校验
    r2_path = f"{results_dir}/result2.csv"
    if os.path.exists(r2_path):
        df2 = pd.read_csv(r2_path, encoding="utf-8-sig")
        valid_opts = [0, 1]
        assert set(df2["是否构成机会"].unique()).issubset(valid_opts), "result2 机会列只能为 0 或 1"
        assert len(df2) == len(df1), f"result2 行数({len(df2)})与 result1({len(df1)})不一致"
        print(f"✅ result2 校验通过 (共 {len(df2)} 条)")
    else:
        print("⚠️ 未生成 result2（等待算法接入）")

if __name__ == "__main__":
    validate_official_csvs()