# 42条Q长度代理说明

独立派生表：`experiments/stage3e3/q_length_proxy_42.csv`。

代理规则仅为正文字符长度：`<80→Q1`、`80–199→Q2`、`≥200→Q3`，得到Q1 3条、Q2 8条、Q3 31条、Q4 0条，与郭报告一致。

该字段命名为`q_length_proxy`，`is_proxy_only=YES`；正式`human_evidence_quality`全部保持空白。长度不能证明来源可靠、需求真实或证据链完整，不能自动填入正式Q档，也不能据此把D3判为通过。
