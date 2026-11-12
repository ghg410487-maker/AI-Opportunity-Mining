import json
import os
import pandas as pd

OUT_DIR = "reports/final_stage1_acceptance"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. 读取现有生成的 rejected_records.csv
rej_df = pd.read_csv(f"{OUT_DIR}/rejected_records.csv", encoding="utf-8-sig")
print(f"原始剔除记录行数: {len(rej_df)}")

# 去重：解决 133 个 B08 重复编号问题
rej_df_unique = rej_df.drop_duplicates(subset=["record_id"], keep="first")
print(f"去重后唯一剔除记录数: {len(rej_df_unique)}")

# 添加语义说明
rej_df_unique["is_recoverable_meaning"] = "原始信息可追溯（原始元数据保存在raw中）"
rej_df_unique.to_csv(f"{OUT_DIR}/rejected_records_final.csv", index=False, encoding="utf-8-sig")

# 2. 处理 dedup_mapping.csv
# 因为历史清洗过程覆盖了"谁是主记录"的日志，我们只能如实说明无法对应。
mapping_df = pd.read_csv(f"{OUT_DIR}/dedup_mapping.csv", encoding="utf-8-sig")

# 新增要求的字段
mapping_df["matched_record_id"] = "UNRECOVERABLE"
mapping_df["matched_batch_id"] = "UNRECOVERABLE"
mapping_df["matched_source_url"] = "UNRECOVERABLE"
mapping_df["match_evidence"] = "历史去重过程未保留主从日志"
mapping_df["verification_status"] = "待核（无法追溯）"

# 特殊处理一些有明确 URL 映射的（如果有的话），但为了绝对诚实，这里全标不可恢复。
mapping_df.to_csv(f"{OUT_DIR}/dedup_mapping_final.csv", index=False, encoding="utf-8-sig")

# 3. 重新生成漏斗
raw_total = 10419
final_total = 1984
rej_total = len(rej_df_unique)

funnel_data = [
    {"stage": "1. 原始抓取总量", "count": raw_total, "desc": "底层实际 raw 行数"},
    {"stage": "2. 最终交付唯一记录", "count": final_total, "desc": "结果CSV行数"},
    {"stage": "3. 被剔除记录(已去重)", "count": rej_total, "desc": "修复了133条重复"},
    {"stage": "3.1 URL/正文重复(无法追溯主记录)", "count": (mapping_df["match_type"]=="URL").sum() + (mapping_df["match_type"]=="CONTENT").sum(), "desc": "历史日志丢失"},
    {"stage": "3.2 短文本/其他过滤", "count": rej_total - ((mapping_df["match_type"]=="URL").sum() + (mapping_df["match_type"]=="CONTENT").sum()), "desc": "规则直接拦截"}
]
pd.DataFrame(funnel_data).to_csv(f"{OUT_DIR}/data_funnel_audit_final.csv", index=False, encoding="utf-8-sig")

# 4. 更新总报告
with open(f"{OUT_DIR}/final_stage1_acceptance_report.md", "w", encoding="utf-8") as f:
    f.write("# 数据资产终审验收报告 (最终版)\n\n")
    f.write("## 修复说明\n")
    f.write("1. **解决重复编号**：修复了 B08 等批次导致的一号多写问题。剔除记录总行数 8435，去重后唯一编号 8302。\n")
    f.write("2. **主记录追溯说明**：在之前的清洗代码中，去重时未保存主从关系日志。因此 `dedup_mapping_final.csv` 中的 `matched_record_id` 全部如实标记为 `UNRECOVERABLE`（无法追溯），**坚决不编造对应关系**。\n")
    f.write("3. **is_recoverable 字段含义**：统一修正为指代“原始元数据是否保存在本地 raw 文件中可供查证”。\n\n")
    f.write("## 数据最终对账\n")
    f.write(f"- 原始 raw 行数：{raw_total}\n")
    f.write(f"- 最终 CSV 记录：{final_total}\n")
    f.write(f"- 剔除唯一编号数：{rej_total}\n")

print(f"✅ 最终修复完成！请查看目录: {OUT_DIR}")