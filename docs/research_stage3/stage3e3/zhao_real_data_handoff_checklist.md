# 给赵的真实数据接口与结果交接清单

稳定接口继续使用`competition_mvp_v1`；`competition_mvp_v1.1`只新增`task2_v2_candidate`，不删除或改名旧字段。

| 交接项 | 路径 | 状态/动作 |
|---|---|---|
| v1统一接口 | `results/stage3e1/unified_records.jsonl` | 稳定默认 |
| v1.1候选接口 | `results/stage3e2/unified_records_v1_1.jsonl` | 功能开关展示 |
| Task 3当前5簇 | `results/stage3e1/result3.csv` | 保持基线 |
| Task 4当前评分 | `results/stage3e1/result4.csv` | 保持基线 |
| 证据约束评分 | `results/stage3e2/result4_evidence_constrained.csv` | 实验展示，不覆盖基线 |
| 算法冻结配置 | `docs/research_stage3/stage3e3/final_algorithm_config.json` | 读取版本号 |
| 郭42条聚合对照 | `docs/research_stage3/stage3e3/guo42_v1_v2_comparison.csv` | 不含原始理由/原文 |
| result2阻断策略 | `docs/research_stage3/stage3e3/result2_binary_policy_pending_approval.md` | 导出按钮继续阻断601条 |

赵的系统不得读取私有`experiments/datasets/`作为公开数据源，不得显示郭的隐藏人工字段。接口切换须由负责人批准并提升版本，不在v1.1中做破坏性修改。
