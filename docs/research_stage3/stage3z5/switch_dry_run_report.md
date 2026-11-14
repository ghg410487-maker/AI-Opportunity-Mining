# 正式结果切换合成数据预演报告

- 日期：2026-11-14
- 脚本：`scripts/switch_official_results.py`
- 测试：`tests/test_switch_official_results.py`
- 日志：`logs/06_switch_dry_run.log`
- 结果：**10 个场景全部通过**

## 1. 合成数据隔离

- 全部使用 `SYNTH-Z5-S00001` ~ `SYNTH-Z5-S00003`，不冒用真实 record_id；
- 仅在 pytest `tmp_path` 中生成，不写入 `competition_submission/`；
- 不伪造真实人工判断；
- 测试结束由 `tmp_path` 清理，不残留测试状态。

## 2. 覆盖场景

| # | 场景 | 预期 | 实测 |
|---|---|---|---|
| 1 | 正常切换 | PUBLISHED，目标文件更新、版本文件写入、备份存在 | PASS |
| 2 | dry-run | DRY_RUN_READY，目标文件不变、不写版本文件 | PASS |
| 3 | 审批标志缺失 | BLOCKED_MANIFEST，目标不变 | PASS |
| 4 | 缺失 result2 | BLOCKED_MANIFEST | PASS |
| 5 | result2 含 REVIEW | BLOCKED_VALIDATION，严格校验输出含 REVIEW | PASS |
| 6 | result3 引用非机会 ID | BLOCKED_VALIDATION | PASS |
| 7 | result4 与 result3 簇集合不一致 | BLOCKED_VALIDATION | PASS |
| 8 | 文件哈希不匹配 | BLOCKED_MANIFEST | PASS |
| 9 | 服务运行中发布 | BLOCKED_SERVICE_RUNNING，目标不变 | PASS |
| 10 | 替换中途失败 | ROLLED_BACK，三份结果字节级恢复，无版本文件残留 | PASS |

## 3. 关键证据

```text
tests/test_switch_official_results.py::test_publish_success PASSED
tests/test_switch_official_results.py::test_dry_run_does_not_modify PASSED
tests/test_switch_official_results.py::test_blocked_without_approval PASSED
tests/test_switch_official_results.py::test_blocked_missing_result2 PASSED
tests/test_switch_official_results.py::test_blocked_review_in_result2 PASSED
tests/test_switch_official_results.py::test_blocked_result3_non_opportunity PASSED
tests/test_switch_official_results.py::test_blocked_result4_cluster_mismatch PASSED
tests/test_switch_official_results.py::test_blocked_hash_mismatch PASSED
tests/test_switch_official_results.py::test_blocked_service_running PASSED
tests/test_switch_official_results.py::test_publish_failure_rolls_back PASSED

10 passed
```

## 4. 当前正式候选状态

`competition_submission/manifest.json`：

- `submission_ready=false`
- `overall_status=NOT_READY`
- 阻断原因：`result2.csv` 0 行占位；严格校验未通过

因此当前执行 `--publish` 会在 manifest 阶段被阻断，不会修改 `results/final`。这是预期行为。

## 5. 发布操作

```bash
# 1. 停止服务
# 2. 预演
python scripts/switch_official_results.py --candidate-dir <candidate> --manifest <candidate>/manifest.json
# 3. 正式发布
python scripts/switch_official_results.py --candidate-dir <candidate> --manifest <candidate>/manifest.json --publish
# 4. 重启服务并验收
run_system.bat
python -m pytest -q
```

失败时脚本自动回滚，并在报告中记录 `backup_dir` 与 `ROLLED_BACK`。