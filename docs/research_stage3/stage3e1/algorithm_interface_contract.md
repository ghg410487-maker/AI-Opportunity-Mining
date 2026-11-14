# 阶段3E-1算法接口契约

版本：`edumine 0.1.0`；接口：`competition_mvp_v1`；决策版本：`task2_rule_v1`。

## 程序入口

- 全流程：`python scripts/run_stage3e1.py`
- 结果校验：`python scripts/validate_stage3e1.py`
- 单元测试：`python -m unittest tests.test_stage3e1`

实现位于`edumine/baselines.py`和`edumine/competition.py`，仅依赖Python标准库，建议Python 3.11及以上。

## 输入

默认只读输入为`data/frozen/result1_Final_All.csv`，字段见`data_schema.md`。真实1984条文件包含可能无再分发许可的第三方正文，不进入公开仓库；赵应从团队批准的受控位置取得，并核对SHA256 `44c75335b3795c746ffc603b339bf6aa4d2e6945e38ebd0a8bcb9d39c9ff0a52`。

`examples/stage3e1/example_input_safe.json`是合成演示，不是CSV运行输入，也不能生成正式官方CSV。

## 输出

主读模型为`results/stage3e1/unified_records.jsonl`，每行一个`competition_mvp_v1`对象。公开字段结构和安全样例见`data_schema.md`与`example_output_safe.json`。

T0分类输出`task2.t0_label`只回答教育相关性；机会判别输出`task2.status`回答是否构成机会，二者不是同一字段，也不存在DIRECT自动映射为1的规则。

内部状态只能是`1`、`0`或`REVIEW`。`REVIEW`必须阻断全量官方result2导出，禁止擅自转为1或0。

## 失败约定

- 输入缺失、表头不符、解析失败或断言失败：程序非零退出，不生成“成功”结论。
- 抽取字段缺失、record_id不一致或证据不能在受控原文中定位：拒绝该增强结果，保留规则结果及失败状态。
- 输出校验失败：不得进入官方CSV导出或系统发布。
- 禁止静默跳过失败记录；异常必须进入日志、阻断表或显式退出。

当前42条机会、5个主题是2026-11-14阶段3E-1基础程序的初步结果，仍需郭进行独立证据与主题审核。
