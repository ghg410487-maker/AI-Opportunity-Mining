# 官方CSV字段映射

| 内部字段 | 官方result2字段 | 规则 |
|---|---|---|
| batch_id | 采集批次号 | 原样 |
| record_id | 记录编号 | 原样且唯一 |
| task2.status | 是否构成机会 | 仅`1→1`、`0→0`；`REVIEW`阻断 |
| task2.confidence | 机会置信度 | 程序值 |
| task2.function_category | 功能类别 | 仅机会1填写，须在官方枚举内 |
| task2.industry | 所属行业 | 仅机会1填写，须在官方枚举内 |

result3来自机器机会1记录的聚类，result4来自主题簇的程序评分。T0标签不属于官方机会字段，不能用`EDUCATION_DIRECT`替代“是否构成机会”。

当前`result2_resolved_subset.csv`只有1389条已决记录；595条`REVIEW`仍阻断全量导出。42条机会和5个主题均为初步程序结果。Mock示例不得用于正式导出。
