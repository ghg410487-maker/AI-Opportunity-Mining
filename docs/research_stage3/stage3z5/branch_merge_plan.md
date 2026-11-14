# Z5-8 分支状态与合并计划

- 日期：2026-11-14
- 当前分支：`integration/stage3e4`
- 最新工程提交：`cd53379`（本报告提交前）
- 远程状态：`git fetch origin` **失败**（`github.com:443` 经本地代理不可达）

## 1. 分支状态

| 分支 | 本地/远程 | HEAD | 说明 |
|---|---|---|---|
| `origin/dev` | 远程缓存 | `bab6db8` | 算法负责人分支，含 v1.1 接口与聚类评分实验 |
| `origin/main` | 远程缓存 | `d73ac6d` | 前端与工程集成基线 |
| `integration/stage3e4` | 本地 | `cd53379` | 工程集成、校验、切换、提交包 |

## 2. 祖先关系

```text
bab6db8 (origin/dev)
   └── d73ac6d (origin/main)
          └── cd53379 (integration/stage3e4)
```

- `git merge-base origin/dev integration/stage3e4` = `bab6db8`（dev 是集成分支祖先）
- `git merge-base origin/main integration/stage3e4` = `d73ac6d`（main 是集成分支祖先）
- 因此集成分支已包含 dev 与 main 的全部提交，三方为线性包含关系。

## 3. 差异统计（本地缓存）

| 对比 | 文件数 | 增删 |
|---|---:|---|
| `origin/dev..integration/stage3e4` | 206 | +55724 / -15 |
| `origin/main..integration/stage3e4` | 53 | +7154 / -53 |

## 4. 冲突检查

- `git merge-tree` 未发现真实冲突标记；
- 输出中的 `ON CONFLICT(record_pk)` 是 SQLite SQL 文本，不是 Git 冲突；
- 由于 dev、main 都是集成分支祖先，当前合并方向不会产生内容冲突。

## 5. 文件分类

| 类别 | 代表路径 | 归属 |
|---|---|---|
| 算法核心 | `edumine/`、`experiments/stage3e3/`、`scripts/run_stage3e2.py`、`scripts/run_stage3e3.py` | 算法负责人 |
| 算法文档 | `docs/research_stage3/stage3e1..e3`（负责人部分） | 算法负责人 |
| 系统工程 | `app.py`、`src/`、`run_system.*`、`requirements.txt`、`scripts/validate_csv.py`、`scripts/switch_official_results.py`、`scripts/security_gate.py`、`scripts/build_submission.py` | 工程负责人 |
| 提交包 | `competition_submission/` | 工程负责人 |
| 测试 | `tests/`（含切换测试与表头测试） | 工程负责人 |
| 验收文档 | `docs/research_stage3/stage3z5/` | 工程负责人 |

## 6. PR / 合并计划

1. **不 push、不强制合并**，等待负责人确认；
2. 建议 PR base：`origin/dev`（算法冻结基线），head：`integration/stage3e4`；
3. PR 说明引用本报告与 `submission_package_audit.md`；
4. 若负责人要求以 `main` 为 base，由于 main 是集成祖先，可直接 fast-forward 合并；
5. 合入前重新 fetch；若 dev 有新算法提交，先在集成分支执行 `git merge origin/dev` 并重跑：
   ```bash
   python -m pytest -q
   python scripts/validate_csv.py --strict
   python scripts/build_submission.py --release
   python scripts/security_gate.py --target competition_submission
   ```
6. 禁止把 `data/`、`results/` 私有产物、盲审文件推送到公开仓库；
7. 禁止覆盖 dev 中的算法文件。

## 7. 远程不可达说明

本轮无法执行 `git fetch origin`，因此：

- 不能确认负责人是否在 `bab6db8` 之后有新提交；
- 不能从远程集成分支 clone；
- 干净环境复现使用本地 `git clone --no-local` 的冻结提交；
- 正式合并前必须恢复网络并重新 fetch。

## 8. 风险

| 风险 | 级别 | 处理 |
|---|---|---|
| 远程不可达，dev 可能已前进 | 中 | 合并前重新 fetch 并预检冲突 |
| 集成分支未 push，评审无法拉取 | 中 | 负责人批准后 push 到远端集成分支 |
| 算法 v2 未冻结，结果可能变化 | 高 | 等待审批后统一重算与切换 |
| 提交包 result2 占位 | 高 | `--release` 阻断，禁止误提交 |