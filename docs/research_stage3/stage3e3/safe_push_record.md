# dev安全同步记录

本记录由执行脚本、公开报告和Git操作结果更新。同步范围只包含阶段3E算法代码、测试、公开实验统计、接口说明和配置；排除冻结主表、私有原文、郭的原始42条CSV、`experiments/datasets/`及无许可快照。

同步前工作区存在大量历史未跟踪文件，当前分支也不是dev。为避免覆盖他人文件，采用“选择性提交→以origin/dev新建隔离worktree→cherry-pick→测试→推送”的方式。最终提交哈希和推送结果见本文件末尾的执行记录。

## 执行记录

- 本地选择性提交：`093da13`。
- 基于`origin/dev@d1f74ae`建立隔离分支`codex/stage3e3-dev-sync`。
- 集成提交：`d91dcda`。
- 隔离worktree测试：24项通过。
- 安全扫描：未包含`experiments/datasets/`、冻结主表、快照、郭原始CSV及含原文的两份核验表。
- 推送：`d1f74ae..d91dcda  HEAD -> dev`，成功。
