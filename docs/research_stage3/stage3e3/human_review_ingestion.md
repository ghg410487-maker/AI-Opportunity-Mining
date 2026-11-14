# 人工核验结果接入说明

## 当前接入状态

郭已完成42条v1机会候选审核，原始CSV以SHA256 `b5ec97ae970885b90f8239d71b6ae52dd615ac05467645460a170d095036a914`保存于私有目录；结果为12/29/1。126条评价集的另外84条仍待完成。

## 郭的其余盲审文件

使用私有文件`experiments/datasets/stage3e3/locked_evaluation_126_guo_blind.csv`。文件不含v1/v2预测、抽样组和权重；顺序已用固定种子重新随机。郭只填写`human_opportunity_label`、`human_reason`、`human_evidence`、`reviewer_id`，完成后把`review_status`设为`COMPLETED`。

不要编辑`eval_id`、`record_id`、来源和原文。不要把该含原文文件提交到公开Git。

## 接入步骤

负责人按`eval_id`把人工字段合并回私有主映射`locked_evaluation_126_private.csv`，保留预测隐藏列原值，然后运行：

```powershell
python scripts/evaluate_stage3e3_human.py --input experiments/datasets/stage3e3/locked_evaluation_126_private.csv
```

脚本仅在126条均形成合法评价标签并完成INSUFFICIENT处置后输出加权v1/v2总体指标；否则返回待审核状态。原始人工字段不得被算法覆盖。当前42条只报告“v1候选精确率审计”，不得报告全量Recall、Accuracy或Macro-F1。
