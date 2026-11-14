# 赵的阶段3E-1集成运行手册

## 环境与验证

```powershell
python --version
python -m unittest tests.test_stage3e1
```

核心实现无第三方Python依赖。不要安装或提交`node_modules`、缓存、密钥或真实原文数据。

## 受控真实运行

1. 从批准的受控位置取得`data/frozen/result1_Final_All.csv`。
2. 核对SHA256：

```powershell
Get-FileHash data/frozen/result1_Final_All.csv -Algorithm SHA256
```

预期为`44c75335b3795c746ffc603b339bf6aa4d2e6945e38ebd0a8bcb9d39c9ff0a52`。

3. 运行并校验：

```powershell
python scripts/run_stage3e1.py
if ($LASTEXITCODE -ne 0) { throw 'stage3e1 run failed' }
python scripts/validate_stage3e1.py
if ($LASTEXITCODE -ne 0) { throw 'stage3e1 validation failed' }
```

4. 系统优先读取`results/stage3e1/unified_records.jsonl`。正式导出前必须检查`official_full_export_ready`；只要存在`REVIEW`就不能把已决子集冒充全量官方result2。

## Mock边界

`examples/stage3e1`内文件均带`SYNTHETIC_DEMO_ONLY`标记，只用于接口联调。禁止把Mock数据、公开审阅表或阶段3D公开索引转换为正式官方CSV。

任何输入、解析、校验或写出失败都必须让流程失败或进入明确阻断清单，不得静默跳过。
