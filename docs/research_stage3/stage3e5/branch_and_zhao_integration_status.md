# 分支与赵的集成状态

核验时远端状态：`main=bdaa4db`，`dev=38b62fb`。用户提供的`integration/stage3e4@8458abd`已不是远端当前尖端；实际远端`integration/stage3e4=473ef57`，共同基线为`bab6db8`。

integration分支包含赵的Web、提交包和切换脚本等大量独立变更；dev新增阶段3E-4审批门控。两者存在真实分支分叉，本轮未合并、未覆盖赵的接口。向赵交付阶段3E-5时应以新的dev提交哈希为算法资料版本，并由赵选择性合入报告/接口，不应把整个研究分支直接覆盖integration。
