# 赵的Stage3E-4集成契约

## 当前可读（实验/历史）

- `data/frozen/result1_Final_All.csv`：1984冻结底表。
- `results/stage3e1/`：v1机器判断和历史Task3/4。
- `results/stage3e2/`：v2实验判断。
- `docs/research_stage3/stage3e3/`：郭42聚合、聚类/评分实验报告。
- `experiments/stage3e4/stage3e4_run_summary.json`：无原文聚合状态。

## 当前不可作为正式提交

全量result2、基于最终机会集合的result3/result4、人工验证的高价值排名。Web系统继续保持v1.1稳定接口，不切换。

## 批准后的切换

负责人审批JSON → `export_official_stage3e4.py`生成候选 → 哈希/Schema验收 → `recompute_task34_stage3e4.py`生成Task3/4候选 → 主题人工审查 → 提交目录发布。切换时需传递文件SHA256、schema、数据/算法/审批版本和`submission_ready=true`；回滚只需恢复上一版本清单，不覆盖历史文件。
