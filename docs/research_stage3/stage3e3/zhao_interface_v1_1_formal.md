# 给赵的正式接口说明

稳定接口仍是`competition_mvp_v1`；现有字段、Task 3—5对象及语义不修改。候选接口`competition_mvp_v1.1`仅新增`task2_v2_candidate`，必须通过功能开关展示，不得替换默认`task2`。

算法冻结候选配置位于`final_algorithm_config.json`。系统需要展示内部状态1/0/REVIEW；正式CSV导出按钮在存在REVIEW时必须禁用并显示阻断数。当前阻断数为601。

聚类和评分实验只写入实验文件，不修改赵正在使用的result3/result4。若后续负责人批准切换，另行提升接口版本，不在v1.1中做破坏性变更。
