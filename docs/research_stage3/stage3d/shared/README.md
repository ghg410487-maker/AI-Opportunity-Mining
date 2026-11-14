# 阶段3D公开共享包

本目录供团队成员从公开仓库读取阶段3D人工标注与负责人裁决成果。

## 文件说明

- `formal180_public_index.csv`：阶段3D-5正式180条T0候选的公开索引。保留记录ID、批次、来源、URL、内容状态、证据类型、内容SHA256和发布来源；不含第三方原文。
- `owner_adjudication_26_final_public.csv`：26条负责人最终裁决的公开版。保留原始双人标签、负责人最终标签、理由、规则、版本和`APPROVED_BY_OWNER`状态；不含第三方原文摘录。
- `owner_review_agreement_10_public.csv`：10条双人一致记录的公开版。保留双人标签、理由、来源、规则和`PENDING`状态；不含第三方原文摘录。
- `owner_adjudication_summary.md`：26条负责人裁决汇总。
- `guideline_draft_0_5.md`：T0教育相关性标注指南草案0.5，尚未冻结为V1.0。
- `t0_guideline_owner_acceptance_checklist.md`：指南负责人审批检查表。
- `annotation_instructions.md`：阶段3D-5双人盲标填写说明，仅作流程背景；实际边界以草案0.5和负责人裁决为准。
- `SHA256SUMS.txt`：本公开共享包内CSV和Markdown文件的SHA256。

## 公开边界

仓库研究协议要求不发布无许可全文。原始180、26和10条CSV包含来自GitHub、哔哩哔哩、掘金及新闻/RSS来源的第三方原文或摘录，尚无逐来源再分发许可登记，因此未提交公开仓库。需要复核正文时，应按`source_url`访问原始来源，并以`content_sha256`核对本地受控副本。

以下负责人专用或敏感工件不在本共享包中：blind_id/共享样本映射、`cross_review_manifest.json`、工作簿、实验缓存和受限原文数据。

公开索引的180条来自阶段3D-5正式发布文件，不是1984条冻结主表。
