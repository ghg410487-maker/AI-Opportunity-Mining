# 官方导出验证

新增`scripts/export_official_stage3e4.py`，按record_id合并冻结主表、版本化机器判断、负责人决定；校验官方表头、1984覆盖、唯一性、二值、0—1置信度、类别值域及0行空类别。

真实运行状态：`BLOCKED`。审批文件为`PENDING_APPROVAL`，601条仍未决；未写出正式`result2.csv`。即使全部审批完成，程序也只先写`result2_candidate_approved.csv`，仍需验收后由提交流程采用正式文件名。

重要阻断：现有内部`opportunity_confidence`未完全证明是官方要求的“成为机会概率”，负责人需批准置信度转换或逐记录值。模板缺失、表头不符、审批未通过、任一REVIEW未决、重复ID或非法类别都会硬阻断。
