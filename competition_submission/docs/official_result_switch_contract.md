# 正式结果切换说明（摘要）

正式结果接入需要：

- `result2.csv`、`result3.csv`、`result4.csv`；
- 输入 `result1.csv` 的 SHA256；
- 算法版本、算法配置版本、负责人审批版本；
- 每份结果文件的 SHA256；
- `approval.submission_ready=true`。

切换命令：

```bash
python scripts/switch_official_results.py \
  --candidate-dir path/to/candidate \
  --manifest path/to/candidate/manifest.json
```

默认只做 dry-run；只有全部审批与严格校验通过后才允许追加 `--publish`。
发布前必须停止服务，发布后重启并执行页面验收；失败会自动回滚到上一版本。
