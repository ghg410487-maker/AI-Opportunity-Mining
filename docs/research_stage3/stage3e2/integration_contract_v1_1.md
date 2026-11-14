# 统一JSONL集成契约v1.1（给赵）

## 兼容承诺

`results/stage3e2/unified_records_v1_1.jsonl`保持v1的`record`、`task2`、`extraction`、`task3`、`task4`、`task5`内容不变；仅把顶层`schema_version`更新为`competition_mvp_v1.1`，并新增`task2_v2_candidate`。自动验证已逐条确认1984条旧字段相等。

新增对象字段：`t0_label`、`dimensions`、`status`、`decision_version`、`evidence_level`、`evidence_quality_score`、`flags`。Web系统应继续以原`task2`作为默认稳定字段；只有显式启用实验开关时才读取`task2_v2_candidate`，界面需标注“候选算法”。

值域不变：内部状态`1/0/REVIEW`；官方输出只接受`1/0`。任何`REVIEW`必须阻断正式result2全量导出。字段变更为加法式版本升级，不要求赵重构现有页面。

本文件即字段变更通知；联调时以`experiments/stage3e2/end_to_end_validation.json`为机器验收依据。
