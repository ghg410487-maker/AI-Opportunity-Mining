# 官方提交包核对清单

- 包版本：`v1-experimental`
- 总体状态：**NOT_READY**
- `submission_ready`：`False`
- 生成时间：2026-11-14T16:42:43

## 1. 阻断项

- result2.csv 数据行数为 0（占位文件）
- 严格校验未通过

## 2. 官方材料核对

| 材料 | 状态 | 说明 |
|---|---|---|
| 四份官方 CSV | NOT_READY | 见 `results/` 与 manifest |
| 源代码 | PASS | `source/` 最小可运行源码 |
| 运行环境说明 | PASS | `docs/environment_and_deployment.md` |
| 系统部署说明 | PASS | 本地运行，公网入口待负责人批准 |
| 系统关键截图 | PASS | `screenshots/` 4 张 |
| AI 使用说明 | PARTIAL | `docs/AI_usage_log.md` 为记录模板，实际记录待团队补填 |
| 论文 Word/PDF | MISSING | 本包未包含论文，需团队另行提交 |
| 附件1标签映射文件 | 待核实 | 官方附件1标签需在最终算法配置中核对 |
| 其他官方材料 | 待核实 | 以赛题 PDF 最终清单为准 |

## 3. 文件清单

| 相对路径 | 大小 | SHA256 前缀 | 状态 |
|---|---:|---|---|
| `docs/AI_usage_log.md` | 2923 | `461abf1f2cdb9155…` | READY |
| `docs/demo_guide.md` | 3385 | `a3cdd744144d171c…` | READY |
| `docs/environment_and_deployment.md` | 930 | `f452d8427d3090c2…` | READY |
| `docs/official_result_switch_contract.md` | 675 | `83582f1f8af32bf5…` | READY |
| `README.md` | 2196 | `08bc4ad74ad3411b…` | READY |
| `results/result1.csv` | 1084788 | `44c75335b3795c74…` | READY |
| `results/result2.csv` | 94 | `93a4de6be0d7476b…` | NOT_READY |
| `results/result3.csv` | 1043 | `8142e768deb7bfd4…` | READY |
| `results/result4.csv` | 443 | `c12d86443e3267ee…` | READY |
| `screenshots/overview.png` | 166780 | `2895b8e949716921…` | READY |
| `screenshots/plan.png` | 123302 | `cfa303802ab9285a…` | READY |
| `screenshots/ranking.png` | 168126 | `6a0f4442eb4470b1…` | READY |
| `screenshots/topics.png` | 254298 | `bbc9d32ed6b6400b…` | READY |
| `source/app.py` | 22947 | `0b3cab053f21a1a7…` | READY |
| `source/config/official_headers.py` | 1073 | `0733ed3e0a426968…` | READY |
| `source/edumine/__init__.py` | 95 | `7055e6acb3374660…` | READY |
| `source/edumine/__main__.py` | 51 | `482b8693e2fe6dbd…` | READY |
| `source/edumine/baselines.py` | 5843 | `b04703796bfcca04…` | READY |
| `source/edumine/cli.py` | 3064 | `5ef66578e579834a…` | READY |
| `source/edumine/competition.py` | 17027 | `6b1510381d816a53…` | READY |
| `source/edumine/core.py` | 23290 | `e61cb01c433a213e…` | READY |
| `source/edumine/normalization.py` | 14829 | `e50aa1d0b9eb9a0b…` | READY |
| `source/edumine/stage3e2.py` | 5663 | `d6b5bc3f0272b70d…` | READY |
| `source/edumine/stage3e3.py` | 2856 | `fb109692e525b938…` | READY |
| `source/requirements.txt` | 79 | `fa7517dcc1612d09…` | READY |
| `source/run_system.bat` | 491 | `819d500ce1bd2ef6…` | READY |
| `source/run_system.sh` | 492 | `cc47aefbfe86ec31…` | READY |
| `source/scripts/switch_official_results.py` | 13410 | `2bbd75492737772a…` | READY |
| `source/scripts/validate_csv.py` | 15405 | `cca31cd0b00e3af0…` | READY |
| `source/src/data_loader.py` | 9024 | `e86d1d60327c7a27…` | READY |
| `submission_checklist.md` | 3944 | `3e5eebb45305f773…` | READY |

## 4. 正式发布闸门

```bash
python scripts/build_submission.py --release
python scripts/validate_csv.py --strict --results-dir competition_submission/results
python scripts/security_gate.py --target competition_submission
```

release 模式在 result2 仍为占位、或严格校验未通过时必须返回非零退出码。

## 5. 排除项

- `.env`、`.env.*`、密钥、SSH 私钥
- `.venv/`、`__pycache__/`、`.pytest_cache/`
- `data/`、`results/` 中间产物、`experiments/datasets/`
- 私有盲审文件、受控人工审核原件
- 本地大文件（`cloudflared.exe`、审计 zip）
