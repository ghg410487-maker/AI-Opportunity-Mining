# 阶段3E-5验收与测试

15项真实数据检查全部通过：84文件哈希、126双ID、14/98/14分布、原始状态保留、XLSX/CSV身份一致、601集合及待批状态、27条唯一且未审批、14条不足、14条正例、5簇12/29/1、正式result2不存在、冻结主表哈希、阶段3E-4导出器保留。

复现命令：

```powershell
python scripts/run_stage3e5.py
python scripts/validate_stage3e5.py
python scripts/generate_stage3e5_docs.py
```

私有逐条映射、人工理由和证据摘录位于Git忽略目录；公开报告只保留必要统计和不含第三方原文的审批表。
