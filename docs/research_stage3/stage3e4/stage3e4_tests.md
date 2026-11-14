# Stage3E-4测试与复现

执行命令：

```powershell
python scripts/run_stage3e4.py
python -m unittest tests.test_stage3e4 -v
python scripts/validate_stage3e4.py
python scripts/export_official_stage3e4.py --template "E:\xwechat_files\wxid_r4to3bbty1yu22_ff68\msg\file\2026-11\result2.csv"
```

单元测试5项全部通过：审批门控、逐记录决定、合法批准构建、重复/非法标签、Task3引用非机会阻断。真实数据验证13项全部通过：冻结主表1984唯一及哈希、601集合、未预填标签、审批待定、正式文件不存在、8条专项误差、27条高优先补证、汇总一致、郭42与源队列/v2哈希未变、补证状态未夸大、Task3/4入口存在。合计18项通过。

导出命令按预期以非零状态阻断，证明未批准规则不会生成正式结果。尚未执行“已批准版本重复运行一致性”，因为当前没有获批输入；这不是伪造通过项，待审批后执行。原始证据核验状态校验目前依赖审批数据结构，后续应在证据增量层加入快照哈希时扩展。
