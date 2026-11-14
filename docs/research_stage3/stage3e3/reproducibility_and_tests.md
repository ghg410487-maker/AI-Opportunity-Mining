# 可复现命令与测试

```powershell
python scripts/run_stage3e1.py
python scripts/run_stage3e2.py
python scripts/run_stage3e3.py
python scripts/validate_stage3e3.py
python -m unittest discover -s tests
```

人工评价完成后：

```powershell
python scripts/evaluate_stage3e3_human.py --input experiments/datasets/stage3e3/locked_evaluation_126_private.csv
```

运行不需要网络和付费API。固定输入SHA256为`44c75335b3795c746ffc603b339bf6aa4d2e6945e38ebd0a8bcb9d39c9ff0a52`。最终验收以`experiments/stage3e3/end_to_end_validation.json`与本目录`SHA256SUMS.txt`为准。
