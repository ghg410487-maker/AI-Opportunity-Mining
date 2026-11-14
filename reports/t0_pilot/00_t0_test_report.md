# T0 教育相关性自动判别 Pilot 测试报告

- 样本总数：42 条
- 判别模型：DeepSeek-V3

## 机器分类分布
- EDUCATION_DIRECT: 19 条
- EDUCATION_WEAK: 12 条
- UNKNOWN: 9 条
- NON_EDUCATION: 2 条

## 边界样本说明
对于空正文、无法获取原文的样本，机器严格输出 UNKNOWN，未做任何强行映射。
待郭的人工标签补充后，将自动计算一致率与 Cohen's Kappa 系数。
