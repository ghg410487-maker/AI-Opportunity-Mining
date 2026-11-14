# 算法接入协议 (V1.0)

本协议用于规范“数据工程”与“核心算法”的对接规范，任何算法模块需遵循此输入输出。

## 1. T0 教育相关性识别 (run_t0)
- **输入**：`List[dict]`，包含 `record_id`, `title`, `content`
- **输出**：`List[dict]`，追加字段 `t0_label` (EDUCATION_DIRECT / EDUCATION_WEAK / NON_EDUCATION / UNKNOWN), `t0_confidence` (float)

## 2. Task 2 机会判别 (run_opportunity_detection)
- **输入**：`List[dict]` (过滤掉 NON_EDUCATION 后的数据)
- **输出**：`List[dict]`，追加字段 `is_opportunity` (1 / 0 / REVIEW), `D1`~`D6` (1/0/U), `evidence_type` (E1~E5), `function_category`, `industry`

## 3. Task 3 主题聚类 (run_clustering)
- **输入**：`List[dict]` (仅包含 is_opportunity=1 的数据)
- **输出**：`List[dict]` 簇列表，包含 `cluster_id`, `topic_name`, `member_record_ids` (List), `source_sites` (int), `representative_record_ids`

## 4. Task 4 价值评估 (run_scoring)
- **输入**：Task 3 的 `List[dict]` 簇列表
- **输出**：`List[dict]`，追加字段 `score` (float), `priority` (int), `score_components` (dict)