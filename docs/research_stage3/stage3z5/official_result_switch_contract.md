# 正式结果交接与原子切换契约

## 1. 交接输入

正式结果接入不能只看文件名，必须同时提供：

| 输入 | 说明 |
|---|---|
| `result2.csv` | 官方全量机会判别，状态仅 0/1，无 REVIEW |
| `result3.csv` | 官方主题聚类，簇内记录必须全部是 result2 机会=1 |
| `result4.csv` | 官方价值评分，簇集合与 result3 一致 |
| 输入 result1 版本 | `result1_sha256` 必须与候选 `result1.csv` 一致 |
| 算法版本 | `algorithm_version` |
| 算法配置版本 | `algorithm_config_version` |
| 负责人审批版本 | `approval.approval_version` |
| 官方标签映射版本 | 功能 16 类 / 行业 30 类核验记录 |
| 文件 SHA256 | 每份结果文件独立哈希 |
| 正式提交标志 | `approval.submission_ready=true` |

## 2. manifest Schema

```json
{
  "schema_version": "official_result_switch_v1",
  "version": "v2-official",
  "algorithm_version": "v2",
  "algorithm_config_version": "v2-config",
  "result1_sha256": "<sha256>",
  "approval": {
    "approved_by": "<负责人>",
    "approval_version": "v2-approval",
    "submission_ready": true
  },
  "files": [
    {"path": "result2.csv", "sha256": "<sha256>", "rows": 1984, "formal": true, "status": "READY"},
    {"path": "result3.csv", "sha256": "<sha256>", "rows": 5, "formal": true, "status": "READY"},
    {"path": "result4.csv", "sha256": "<sha256>", "rows": 5, "formal": true, "status": "READY"}
  ]
}
```

## 3. 原子切换流程

脚本：`scripts/switch_official_results.py`

1. 在隔离目录读取候选文件；
2. 校验 manifest 结构、审批标志、版本字段、result1 哈希；
3. 逐文件校验 SHA256、行数 > 0、formal=true、status=READY；
4. 运行 `validate_csv.py --strict --results-dir <candidate>`；
5. 校验同版本哈希一致性，禁止同版本不同内容覆盖；
6. 检测 8501 服务是否运行；服务运行时拒绝发布；
7. 备份当前 `result2/3/4`、版本文件和中间产物；
8. 写入临时目录并再次校验哈希；
9. 全部就绪后依次替换，写 `.result_version.json`；
10. 失败时从备份完整回滚，删除临时文件；
11. 发布后重启服务并执行页面验收。

**禁止**先切 result2 再等待 result3/4。多文件替换期间必须停止服务，重启后一次性加载新版本。

## 4. 命令

```bash
# 只预演，不修改
python scripts/switch_official_results.py \
  --candidate-dir path/to/candidate \
  --manifest path/to/candidate/manifest.json

# 正式发布（必须先停止 8501 服务）
python scripts/switch_official_results.py \
  --candidate-dir path/to/candidate \
  --manifest path/to/candidate/manifest.json \
  --publish
```

退出码：

- `0`：`DRY_RUN_READY` 或 `PUBLISHED`
- `1`：校验/切换失败，已回滚（`ROLLED_BACK`）
- `2`：阻断（`BLOCKED_MANIFEST` / `BLOCKED_VALIDATION` / `BLOCKED_VERSION` / `BLOCKED_SERVICE_RUNNING`）

## 5. 禁止事项

- `submission_ready=false` 时禁止修改目标目录；
- 禁止把 REVIEW 映射为 0/1；
- 禁止 v1 result3/4 与 v2 result2 混装；
- 禁止在服务运行中直接覆盖结果文件；
- 禁止跳过 manifest 哈希和严格校验。