# T0标注指南 draft-0.6候选

版本日期：2026-11-14
状态：基于draft-0.5、26条历史负责人裁决与郭的审批摘要形成的候选稿，**未经负责人批准，不是T0 V1.0冻结版**。

## 1. 分层管理

1. T0教育相关性：`EDUCATION_DIRECT / EDUCATION_WEAK / NON_EDUCATION / UNKNOWN`。
2. 场景S：`S1教师教学支持 / S2学生学习支持 / S3实验与实践教学 / S4教育管理与评价 / OTHER_EDUCATION / UNKNOWN`。
3. 证据性质E：`E1用户直接需求 / E2机构行动 / E3学术研究 / E4市场供给 / E5技术可行性`；无法判断时留空，E5不得作兜底。
4. 证据质量Q：`Q0不可核实 / Q1很弱 / Q2有限 / Q3较可靠 / Q4高可靠`。
5. Task 2 D1—D6：教育相关性、问题明确性、需求真实性、AI核心性、可行性、未满足程度。

T0、S、E、Q与D1—D6必须独立存储。T0 DIRECT不等于真实需求或AI机会；E4产品供给不等于D3通过；Q高不等于机会价值高。

## 2. T0四分类

- DIRECT：主要对象、实际用途或明确功能直接服务教学、学习、评价、实验实践、培训、教师发展或教育管理。
- WEAK：教育用途是次要但可解释的场景，或证据仅能建立教育关联，尚不足以确认教育任务为核心。
- NON：主旨明确为非教育活动，教育词只是身份、地点、修辞或偶然例示。
- UNKNOWN：材料缺失、损坏或不可解释，无法可靠选择前三类；不得用来回避边界判断。

可信标题若明确主体和具体教育任务，可以在有限范围支持T0判断，但必须标记标题级证据；不能推断流程、效果、需求真实性或全文主旨细节。不得使用“80字”或任何固定字数作为机械标签阈值。

## 3. 统一证据层级

| evidence_level | 含义 | 可支持范围 |
|---|---|---|
| `FULL_TEXT` | 原始完整正文、README或Issue | 主旨、任务和流程 |
| `ABSTRACT` | 可核验正式摘要 | 摘要覆盖范围内结论 |
| `SUBSTANTIVE_FRAGMENT` | 有实质信息的正文片段 | 片段明确支持的事实 |
| `SHORT_CONTENT` | 短正文但并非只有标题 | 仅限明确出现的内容 |
| `TITLE_ONLY` | 可信标题 | 明确主体/用途；不得冒充正文 |
| `AUXILIARY` | 镜像、转载或同题新闻 | 补充上下文，不升级为原始全文 |
| `UNAVAILABLE` | 内容不可用 | 通常进入UNKNOWN或补证 |

历史值映射：`SUBSTANTIVE_OR_FRAGMENT→SUBSTANTIVE_FRAGMENT`；`TITLE_LIKE→TITLE_ONLY`仅在确认内容确为标题时映射；不能仅按字数自动映射。

## 4. 来源恢复状态

`NOT_REQUESTED`、`RECOVERED_FULL`、`RECOVERED_PARTIAL`、`ORIGINAL_NOT_RECOVERABLE_AUXILIARY_FOUND`、`SOURCE_UNAVAILABLE`。`NOT_REQUESTED`不得写成“已核验全文”。无原始快照时如实记录状态；SHA256只在实际存在可访问快照或文件时填写，不为满足格式编造不存在的哈希。

## 5. confidence

统一使用`HIGH / MEDIUM / LOW`：HIGH表示证据直接且相邻标签排除清晰；MEDIUM表示结论可作但存在来源或上下文限制；LOW表示材料有限、需优先复核。confidence衡量判断稳定性，不是模型概率、Q等级、需求强度或价值分。

## 6. 填写与历史事实

每条至少保存record_id、T0标签、主旨摘要、可定位证据、理由、evidence_level、source_recovery_status、confidence、URL；S/E/Q和D1—D6按任务层独立填写。原始标注不得被负责人裁决或机器结果覆盖。

26条历史负责人裁决继续作为案例层保留，分布DIRECT 22、WEAK 3、NON 1。共同36条原始一致率27.78%、Kappa 0.093023继续如实报告，不因后续裁决反向修改。低一致率意味着规则执行仍需校准，不证明历史人工结果已经成为充分验证的金标准。

## 7. 版本边界

本稿只解决枚举、字段和证据限制的一致性。Q1—Q3若存在经负责人确认的V0.2更细定义，应在批准时合并；在此之前，疑难项标记`REVIEW_Q_RULE`。本稿不冻结V1.0。
