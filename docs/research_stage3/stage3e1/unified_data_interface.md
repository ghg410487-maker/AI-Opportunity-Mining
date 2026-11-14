# Task 2—5统一数据接口

## 主记录接口

`results/stage3e1/unified_records.jsonl`每行一个`competition_mvp_v1`对象：

- `record`：batch_id、record_id、source_name、source_url；
- `task2`：T0标签、六维得分、内部机会状态、置信度、官方功能/行业候选；
- `extraction`：用户、任务、痛点、现有方案、原文证据、来源ID、抽取方式、校验状态；
- `task3`：仅机会=1记录有cluster_id与cluster_name；
- `task4`：仅已聚类记录有总分和维度分；
- `task5`：是否进入推荐集。

该接口是后续API、仪表盘和策划案的唯一聚合读模型；原始数据、人工标注、机器判别仍保存在各自独立数据层。

## Task 2状态与官方result2映射

| 内部状态 | 含义 | 官方映射 |
|---|---|---|
| `1` | 六维规则均达到最低门槛 | `是否构成机会=1` |
| `0` | 明确非机会或关键维度同时缺失 | `是否构成机会=0` |
| `REVIEW` | 信息/规则不足，需复核 | **阻断正式全量导出** |

当前提供`result2_resolved_subset.csv`用于字段和值域联调，提供`result2_export_blockers.csv`记录REVIEW。前者不是正式全量提交文件。

## 六维判别

1. `education_relevance`：T0教育相关性，只作筛选门控；
2. `problem_clarity`：问题/任务是否明确；
3. `demand_authenticity`：是否存在用户或机构的真实需求信号；
4. `ai_core`：AI是否为核心解决能力；
5. `feasibility`：是否存在可落地技术/方案信号；
6. `unmet_degree`：现有方案是否仍存在缺口。

T0 DIRECT不能直接生成机会=1。

## 抽取与LLM成本控制

`CachedNeedExtractor`先运行规则抽取。只有规则缺少任务和痛点、且调用方显式注入LLM函数时，才执行LLM回退。返回JSON必须字段齐全、record_id一致、证据逐字存在于原文，否则拒绝；合法结果按“record_id+正文”SHA256缓存。本次真实运行未注入LLM，调用数为0。

## Task 3—5接口

- Task 3输入：仅`task2.status=1`；输出官方`result3.csv`和统一接口中的cluster信息。
- Task 4输入：聚类统计与六维证据；输出官方`result4.csv`。分数由程序化归一化和固定权重计算，不由LLM评分。
- Task 5输入：排序主题、抽取证据和来源ID；输出`recommendations.json`与`plans/*.md`。
