# 郭剩余84条受控盲审交付说明

## 发放文件

仅发放私有文件：

`experiments/datasets/stage3e3/locked_evaluation_remaining84_guo_blind.csv`

SHA256：`d2d1982cb48fdded8e414b752b1b12155b19427561d9653d3ec58886aa1804d9`

该文件由原126条锁定盲审表过滤已完成的42条得到，没有重新抽样或改变样本集合。84个eval_id、record_id均唯一；保留原blind_order。文件不含v1/v2预测、抽样层、权重或机器判别字段。

## 郭需要填写

只填写这84条的：

- `human_opportunity_label`：`1`、`0`或`INSUFFICIENT`；
- `human_reason`：判断理由；
- `human_evidence`：可定位证据，材料不足时说明缺失项；
- `reviewer_id`：郭；
- `review_status`：完成后改为`VERIFIED`。

不要修改`eval_id`、`record_id`、来源、原文、evidence_level或blind_order。不要再次审核已完成的42条。含第三方原文的文件只能受控传递，不得Push到公开GitHub。

原126条盲审文件哈希：`0fcfd16443fe85c77462f909b80626885631c6b83caf0e30d95ea0702234bbe6`。42条接入后的私有映射哈希：`bce8a347ad1a4f2c77ed67fda8c47e2437575c90a69b0ba3881206c5a55c7d87`。
