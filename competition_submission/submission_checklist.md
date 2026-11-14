# 官方提交包核对清单（v1 占位包）

- 包状态：**SHELL / NOT_READY**（等待 result2 REVIEW 政策批准后重算）
- 数据口径：**v1 实验数据**（42 机会 / 595 REVIEW）
- 生成日期：2026-11-14
- 来源分支：`integration/stage3e4`

## 1. 包内文件

| 文件 | 行数（不含表头） | 来源 | SHA256 |
|---|---:|---|---|
| `result1.csv` | 1984 | `results/final/result1_Final_All.csv` | `44c75335b3795c746ffc603b339bf6aa4d2e6945e38ebd0a8bcb9d39c9ff0a52` |
| `result2.csv` | 0（仅表头占位） | 官方表头，待 REVIEW 审批后重算 | `93a4de6be0d7476bbfac8a31636b22eadf29004832acc067e52e0cf6fc764947` |
| `result3.csv` | 5 | `results/final/result3.csv`（列名已对齐官方模板，`来源覆盖`=独立来源数） | `4f0b1a76aeff54960b86fe91e25b07d1b788bb32e86acf5319762cd38e32e6bc` |
| `result4.csv` | 5 | `results/final/result4.csv` | `c12d86443e3267ee3b01fbc7aef577c65a0248f1a62930dd42cfea04aef3da45` |

## 2. result2 状态说明

`result2.csv` **只有官方表头，没有数据行**，原因：

- v1 当前有 **595 条 REVIEW** 未决，另有 1389 条已决记录；
- REVIEW 表示政策未定，**禁止映射为 0 或 1**；
- 官方 result2 要求同一批次全量记录，因此在政策批准前不能生成合规全量 result2；
- 已决子集与阻断表保留在 `results/final/result2_resolved_subset.csv`、`results/final/result2_export_blockers.csv`，供审批和重算使用。

## 3. v1 / v2 隔离声明

- 本提交包仅使用 v1 数据：**42 机会 / 595 REVIEW / 5 个主题簇**；
- **未混入**负责人 v2 结果：**16 机会 / 601 REVIEW**；
- v2 材料仅存在于 `docs/research_stage3/stage3e3/` 与 `experiments/stage3e3/`；
- 最终政策批准后，统一重算 result2 / result3 / result4，再替换本包文件。

## 4. C004 说明

- `result3.csv`、`result4.csv` 保留 C004 机器实验历史；
- Web 系统推荐视图已暂停展示 C004（人工核验 0/5 确认）；
- 提交包中的机器结果不做人工篡改，审批时需同时查看 `experiments/stage3e3/cluster5_guo_initial_audit.csv`。

## 5. 校验命令与预期

```bash
# 预览模式：允许 REVIEW，部分通过，EXIT=0
python scripts/validate_csv.py

# 严格正式提交模式：当前预期 NOT_READY + EXIT=1
python scripts/validate_csv.py --strict
```

当前严格模式阻断原因：`result2 仍有 595 条 REVIEW 未决`。在 REVIEW 清零并完成 100% 对账前，不得把本包标记为正式提交版。

## 6. 打包排除项

以下内容不得进入提交包或压缩包：

- `.env`、`.env.*`（已移除真实密钥，仅保留 `.env.example`）
- `.venv/`、`venv/`、`__pycache__/`、`.pytest_cache/`、`*.pyc`
- `cloudflared.exe`（约 55 MB 本地工具）
- `*.zip`（B08/B10 审计包等本地材料）
- `.codeartsdoer/`、`.workbuddy/`、`.wbapp_*.genie`
- `data/`、`results/` 中间产物（`competition_submission/` 除外）
- `experiments/datasets/` 私有评测数据

## 7. 提交前核对

- [x] 四份 CSV 文件名与官方一致
- [x] result1/result3/result4 来自 v1 真实产物
- [x] result2 保留官方表头，未伪造 REVIEW 映射
- [x] 包内无 `.env`、无密钥、无缓存目录
- [x] v1/v2 数量口径已在清单中声明
- [x] 已知悉当前为 `NOT_READY`，等待 REVIEW 政策批准
- [ ] 负责人批准 REVIEW 处置政策
- [ ] 重算全量 result2 并替换占位文件
- [ ] 重跑 `python scripts/validate_csv.py --strict` 得到 `READY_FOR_SUBMISSION`
- [ ] 更新 SHA256 与本清单状态为 `READY`