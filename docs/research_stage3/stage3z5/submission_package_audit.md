# Z5-2 官方提交包完整性审查

- 包路径：`competition_submission/`
- 当前状态：**SHELL / NOT_READY**
- 版本：`v1-experimental`
- manifest：`competition_submission/manifest.json`（同时归档为 `submission_manifest.json`）

## 1. 官方材料核对

依据 `docs/competition_compliance.md`（其声明依据官方赛题 PDF、附件1、附件2与四份空模板）。

| 官方材料 | 状态 | 证据 / 缺口 |
|---|---|---|
| 四份官方 CSV | PARTIAL | `results/result1.csv` 1984 行；`result3.csv` 5 行；`result4.csv` 5 行；**`result2.csv` 0 行占位** |
| 源代码 | PASS | `source/` 含 app、src、edumine、config、校验与切换脚本、启动脚本 |
| 运行环境说明 | PASS | `docs/environment_and_deployment.md` |
| 系统部署说明 | PARTIAL | 仅本地运行，稳定公网入口待负责人批准 |
| 系统关键截图 | PASS | `screenshots/` 4 张（已脱敏，无绝对路径） |
| AI 使用说明 | PARTIAL | `docs/AI_usage_log.md` 仅模板，真实记录为空 |
| 论文 Word/PDF | **MISSING** | 本包未包含论文，需团队另行提交 |
| 官方附件1标签映射 | **待核实** | 功能 16 类/行业 30 类需在最终算法配置中逐项核对 |
| 其他官方材料 | 待核实 | 以赛题 PDF 最终清单为准 |

不得把“文件存在”当作“材料合格”。四份 CSV 已做行数、ID 唯一性、值域和跨表一致性检查。

## 2. 包结构与规范

```text
competition_submission/
├── results/        # result1..result4.csv
├── source/         # 最小可运行源码（非整仓复制）
├── docs/           # README、环境、切换、演示、AI 使用
├── screenshots/    # 4 张关键页面
├── README.md
├── submission_checklist.md
└── manifest.json
```

- `manifest.json` 记录 31 个文件的相对路径、大小、SHA256、用途、版本、formal 标志、状态和校验结果。
- `source/` 已实测可在包内独立启动：`AppTest` 无异常，读取 1984 条记录（通过 `../results` 数据根回退）。
- 不复制 `.venv/`、`data/`、`results/` 中间产物、私有盲审文件、审计 zip。

## 3. 占位文件阻断验证

`result2.csv` 只有官方表头、0 行数据。三层阻断均生效：

| 命令 | 结果 |
|---|---|
| `python scripts/build_submission.py --release` | `RELEASE_BLOCKED`，EXIT=1 |
| `python scripts/validate_csv.py --strict --results-dir competition_submission/results` | `NOT_READY`，EXIT=1 |
| `python scripts/switch_official_results.py ...` | `submission_ready=false` 时 `BLOCKED_MANIFEST`，不修改目标 |

校验不只看文件是否存在，还检查：

- 数据行数 > 0；
- result2 状态仅 0/1，REVIEW 不得映射；
- result2 与 result1 100% 对账；
- result3 簇内记录必须全部是 result2 机会=1 且无重复；
- result4 与 result3 簇集合、行数一致；
- manifest SHA256 与文件实际哈希一致。

## 4. 本机审查发现并修复

1. **result3 官方表头冲突**：`config/official_headers.py` 原写“来源覆盖/簇内机会记录”，与官方模板“来源网站数/簇内机会记录编号”不一致。已按官方模板修正，并重建提交包。
2. **提交包 source 路径不可运行**：源码只读 `results/final/`，包内是 `results/`。已增加数据根回退与官方文件名候选，包内 AppTest 实测通过。
3. **截图泄漏绝对路径**：原截图侧边栏显示 `E:\AIjiaoyu\...`，已改为相对路径并重新截图，扫描无泄漏。

## 5. 版本一致性

- `manifest.version = v1-experimental`；
- `result1/result3/result4` 均来自同一冻结源目录；
- `result2` 占位，formal=false、status=NOT_READY；
- 禁止把当前 v1 result3/4 与未来 v2 result2 混装；正式切换必须整包版本一致。

## 6. 结论

除正式算法结果（result2 全量）外，还缺：

1. 论文 Word/PDF；
2. 真实 AI 使用记录；
3. 附件1标签映射的最终核验；
4. 稳定公网部署与访问说明（如需）；
5. 负责人对 REVIEW 处置政策的审批。