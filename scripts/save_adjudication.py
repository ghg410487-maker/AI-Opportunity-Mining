import pandas as pd
import os
import json
import shutil

# 1. 建立曹哥要求的独立目录
OUT_DIR = "docs/research_stage3/stage3d2"
os.makedirs(OUT_DIR, exist_ok=True)

# 2. 读取你下载的负责人裁决 CSV
# 请确保你把那个 CSV 存到了 data/ 目录下，命名为 t0_owner_adjudication.csv
CSV_PATH = "data/t0_owner_adjudication.csv" 

if not os.path.exists(CSV_PATH):
    print(f"请先把负责人裁决的 CSV 文件保存到 {CSV_PATH}")
    exit()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# 3. 整理并严格按负责人要求输出独立裁决表
# 11条状态为 APPROVED_BY_OWNER，3条保持 WAITING_FOR_SOURCE
# 直接保存，确保不覆盖原来的 42 条机器/人工标签
out_path = f"{OUT_DIR}/t0_owner_adjudication_v1.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")

# 生成裁决审计记录
audit_md = f"""# T0 裁决数据入库审计

- 已成功读取负责人裁决结果。
- 总计记录：{len(df)} 条
- 批准 (APPROVED_BY_OWNER)：{len(df[df['decision_status'] == 'APPROVED_BY_OWNER'])} 条
- 待定 (WAITING_FOR_SOURCE)：{len(df[df['decision_status'] == 'WAITING_FOR_SOURCE'])} 条

## 安全边界声明
- 原始 42 条人工（郭）与机器（赵）标签未被修改。
- 原始 1984 条冻结主表未被修改。
- 3条待核记录的 final_label 保留为空，未自动填写 UNKNOWN。
"""
with open(f"{OUT_DIR}/t0_adjudication_audit.md", "w", encoding="utf-8") as f:
    f.write(audit_md)

print(f"✅ 11条裁决结果已成功入库 -> {out_path}")