# 阶段3E-1数据Schema

## 受控输入CSV

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| 采集批次号 | string | 是 | 批次标识 |
| 记录编号 | string | 是 | 全局唯一记录ID |
| 来源网站名称 | string | 是 | 来源名称 |
| 来源链接 | string/URL | 是 | 原始来源URL |
| 内容 | string | 是 | 受控原文；不得无许可公开 |
| 采集时间 | ISO-8601 string | 是 | 采集时间 |
| 热度指标（点赞数、评论数、收藏数、转发量等） | mapping string | 否 | 仅解析非负数值 |

## 统一输出JSONL

| 路径 | 类型 | 说明 |
|---|---|---|
| schema_version | string | 固定为`competition_mvp_v1` |
| record | object | batch_id、record_id、source_name、source_url |
| task2.t0_label | enum | EDUCATION_DIRECT/WEAK/NON/UNKNOWN，教育相关性 |
| task2.dimensions | object | 六维0—2程序得分 |
| task2.status | enum | `1`、`0`、`REVIEW`，机会判别结果 |
| task2.confidence | number | 程序置信度，不是人工可信度 |
| extraction | object | 受控环境内的结构化抽取；公开版不得携带无许可原文 |
| task3 | object/null | 仅机器机会=1记录具有主题簇 |
| task4 | object/null | 主题程序评分及维度 |
| task5 | object/null | 是否进入机器推荐集 |

六维字段为`education_relevance`、`problem_clarity`、`demand_authenticity`、`ai_core`、`feasibility`和`unmet_degree`。

真实JSONL含受控证据摘录，仅留在本地或合规受控环境。GitHub只保存Schema、安全合成示例、代码和统计摘要。
