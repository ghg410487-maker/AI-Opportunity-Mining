# 赵的 Web 系统集成验收报告（Stage 3E-3 / Stage 3E-4 修复）

- 验收日期：2026-11-14
- 当前分支：`integration/stage3e4`
- 算法基线：`origin/dev` commit `bab6db8`（fix(stage3e3): skip private handoff check in public clone）
- 本地合并提交：`c76c12e`（Merge remote-tracking branch 'origin/dev'）
- 运行环境：Python 3.12 / Streamlit 1.67 / pandas 3.1.1 / Windows
- 数据源：`results/final/result1_Final_All.csv`（1984 条）

## 0. 数据版本声明（重要）

当前 Web 系统展示、校验和验收的均为 **v1 实验数据**：

- 机会：**42 条**（`task2.status=1`）
- REVIEW 阻断：**595 条**（`result2_export_blockers.csv`）
- 主题聚类：v1 机器结果 5 个簇（`result3.csv`）
- 机会评分：v1 机器结果 5 条（`result4.csv`）

本分支 **不混入** 负责人的 **v2 结果（16 机会 / 601 REVIEW）**。v2 结果目前仅作为算法端实验与待审批材料存在于 `docs/research_stage3/stage3e3/` 与 `experiments/stage3e3/`，未写入 `results/final`，也未接入页面、校验器和验收数据。

**最终政策批准后，再以统一口径重算 result2 / result3 / result4，并同步更新页面与校验报告。** 在此之前不得把 v1 与 v2 的数量混用，也不得把 REVIEW 映射为 0 或 1。

## 1. 本次更新的代码

### 1.1 `app.py`

| 变更 | 说明 |
|---|---|
| 真实结果读取 | 继续读取 `results/final/result3.csv`、`result4.csv`，保留真实机器实验结果，不替换为 Mock |
| C004 暂停展示 | 读取 `experiments/stage3e3/cluster5_guo_initial_audit.csv`，将 `human_confirmed_1=0` 且 `human_rejected_0>0` 的簇识别为人工全否簇；当前为 `T3-C004`，并在 `result3`/`result4` 推荐视图中过滤 |
| 暂停提示 | 两个视图保留小字提示：“C004 簇因人工核验全否，已在推荐视图中暂停展示（保留机器实验历史）” |
| 实验候选水印 | 三个页面顶部保留“⚠️ 【实验候选版本】…”警告，声明非正式提交版 |
| 排行重排 | 过滤 C004 后仅重算页面展示“排名”，机器原始“优先级”保留不变 |
| 策划案下载 | 新增“⬇️ 下载 Markdown 文件”按钮，按所选主题簇编号下载 `plan_T3-Cxxx.md` |
| 同名主题修复 | 策划案主题选择改为“簇编号 + 名称”，避免三个“学生-文本生成机会”无法区分 |
| REVIEW 约束 | 未修改任何 `REVIEW → 0/1` 映射逻辑 |

### 1.2 `scripts/validate_csv.py`

在四份 CSV 核对基础上新增 **严格正式提交模式**：

- 预览模式（默认）：存在 REVIEW 时输出“部分通过 / 待 REVIEW 审批”，退出码 `0`；
- 严格模式（`--strict`）：只要 result2 存在任何 REVIEW、result2 未与 result1 100% 对账、或四份 CSV 不齐全，即输出 `NOT_READY` 并返回退出码 `1`，防止打包误判；
- 保留 result1 行数与 ID 唯一性、result2 已决/阻断对账、result3 簇与记录核对、result4 簇集合与分数核对。

用法：

```bash
# 预览模式：允许部分通过，EXIT=0
python scripts/validate_csv.py

# 严格正式提交模式：不满足正式提交条件时 NOT_READY，EXIT=1
python scripts/validate_csv.py --strict
```

### 1.3 `tests/test_headers.py`

修复历史夹具缺失导致的遗留失败：

- 优先使用当前真实官方表头文件 `results/final/result1_Final_All.csv`；
- 兼容历史路径 `results/B01/result1.csv`（存在时使用）；
- 两者都不存在时，使用 `tmp_path` 生成仅含官方表头的 Mock CSV 兜底，避免测试因缺文件失败；
- 测试仍然校验 `config.official_headers.RESULT1` 的完整列顺序。

## 2. 校验日志

### 2.1 预览模式（EXIT=0）

```text
=== 官方四份 CSV 核对 ===
目录：E:\AIjiaoyu\results\final
模式：预览模式
✅ result1 行数 1984，记录编号唯一
✅ result2 已决子集 1389 条，记录编号唯一，状态仅 0/1
✅ result2 REVIEW 阻断表 595 条，记录编号唯一
✅ result2 与 result1 对账一致：1389 已决 + 595 REVIEW = 1984
✅ result3 共 5 个主题簇，主题簇编号唯一
✅ result3 簇内记录 42 条，无重复
✅ result3 与 result2 机会记录对账一致：42 条
✅ result4 共 5 条评分记录，主题簇编号唯一
✅ result4 与 result3 主题簇集合一致
✅ result4 与 result3 行数一致
✅ result4 机会价值分范围 6.28-94.38
✅ result4 优先级唯一

=== 校验摘要 ===
• result2：部分通过（已决 1389 条，待 REVIEW 审批 595 条），REVIEW 保持阻断，禁止正式全量导出
校验结果：部分通过（result2 待 REVIEW 审批，其余 CSV 核对通过）
EXIT=0
```

### 2.2 严格模式（EXIT=1）

```text
=== 官方四份 CSV 核对 ===
目录：E:\AIjiaoyu\results\final
模式：严格正式提交模式（--strict）
...
=== 校验摘要 ===
• result2：部分通过（已决 1389 条，待 REVIEW 审批 595 条），REVIEW 保持阻断，禁止正式全量导出
NOT_READY
严格模式阻断原因：result2 仍有 595 条 REVIEW 未决
EXIT=1
```

说明：当前 `result2_export_blockers.csv` 实际为 595 条；Stage 3E-3 的 `review601_disposition_queue.csv` 为 601 条待处置队列，属于负责人 v2 材料。校验脚本按实际文件动态统计，601/595 均保持 REVIEW 阻断，未映射为 0 或 1。

## 3. 测试日志

```text
$ python -m pytest -q
.........................                                                [100%]
25 passed in 3.68s
```

```text
[数据概览]     exceptions=0  warnings=0  C004提示=False  下载按钮=0
[机会主题发现] exceptions=0  warnings=1  C004提示=True   表格行数=4
[机会价值排行] exceptions=0  warnings=1  C004提示=True   表格行数=4
[机会策划案]   exceptions=0  warnings=1  C004提示=True   下载按钮=1
```

- pytest 全绿（25 passed，0 failed）；
- AppTest 四个页面均无异常；
- 主题发现与排行均只展示 4 个簇（C002/C005/C001/C003），C004 被过滤；
- 策划案主题选项不含 C004，下载按钮可用（`disabled=False`）；
- `streamlit run app.py` 启动成功，HTTP 200。

## 4. 分支与 PR 对比说明

| 项目 | 内容 |
|---|---|
| 集成分支 | `integration/stage3e4` |
| 创建基线 | `main`（最新 `d73ac6d`，已包含 `origin/dev` 算法与前端联调） |
| 算法基线 | `origin/dev`（`bab6db8`） |
| 建议 PR base | `origin/dev` |
| 建议 PR head | `integration/stage3e4` |
| 相对 `origin/dev` | 新增前端入口、数据加载层、四表校验器、测试兜底、验收报告与截图等集成内容 |
| 相对 `main` | 本轮新增 3 个文件改动：`scripts/validate_csv.py`、`tests/test_headers.py`、本验收报告 |

PR 对比要点：

1. **算法与前端来自同一条可复现历史**：`origin/dev@bab6db8` 已合并到本地，集成分支在其之上补齐前端与校验层；
2. **算法代码不改**：`edumine/` 与 `experiments/stage3e3/` 保持负责人提交内容，不把 v2 实验材料混入 `results/final`；
3. **产物可重算**：`results/final` 为本地生成且被 `.gitignore` 忽略，合入后需运行 `python -m edumine competition-mvp --input results/final/result1_Final_All.csv --output results/final` 重算；
4. **正式提交闸门**：CI/打包前必须运行 `python scripts/validate_csv.py --strict`，当前预期为 `NOT_READY`（595 条 REVIEW 未决），政策批准并重算后才允许变为 `READY_FOR_SUBMISSION`。

## 5. 关键页面截图

| 页面 | 截图路径 |
|---|---|
| 数据概览 | `docs/research_stage3/stage3e3/screenshots/overview.png` |
| 机会主题发现（C004 已暂停） | `docs/research_stage3/stage3e3/screenshots/topics.png` |
| 机会价值排行（C004 已暂停） | `docs/research_stage3/stage3e3/screenshots/ranking.png` |
| 机会策划案（含下载按钮） | `docs/research_stage3/stage3e3/screenshots/plan.png` |

截图由 Playwright + 本机 Chrome 在 1500×1200 视口下自动生成，均为真实运行页面。

## 6. 当前系统文件保存路径

| 类型 | 路径 |
|---|---|
| Web 入口 | `app.py` |
| 数据加载层 | `src/data_loader.py` |
| CSV 校验脚本 | `scripts/validate_csv.py` |
| 原始数据 | `results/final/result1_Final_All.csv` |
| 机会判别已决子集 | `results/final/result2_resolved_subset.csv`（1389 条） |
| REVIEW 阻断表 | `results/final/result2_export_blockers.csv`（595 条） |
| 主题聚类结果 | `results/final/result3.csv`（5 簇，C004 仅暂停展示、文件保留） |
| 机会评分结果 | `results/final/result4.csv`（5 条，C004 仅暂停展示、文件保留） |
| 统一读模型 | `results/final/unified_records.jsonl`（1984 行，`competition_mvp_v1`） |
| 推荐与策划案 | `results/final/recommendations.json`、`results/final/plans/` |
| C004 人工审计依据 | `experiments/stage3e3/cluster5_guo_initial_audit.csv` |
| 表头基线测试 | `tests/test_headers.py` |
| 本验收报告 | `docs/research_stage3/stage3e3/zhao_acceptance_report.md` |

## 7. 约束确认

- [x] 已拉取并合并 `origin/dev` 最新提交 `bab6db8`
- [x] 当前展示为 v1 实验数据（42 机会 / 595 REVIEW），未混入 v2（16 机会 / 601 REVIEW）
- [x] 使用真实 `result3.csv`、`result4.csv`，未删除、未替换 Mock
- [x] C004 人工全否簇已从推荐视图过滤，并保留说明
- [x] 页面顶部保留实验候选、非正式提交版警告
- [x] 595/601 条 REVIEW 均未映射为 0 或 1
- [x] 策划案支持下载 Markdown
- [x] `validate_csv.py --strict` 在 REVIEW 未决时输出 NOT_READY 并返回非零退出码
- [x] pytest 全绿（25 passed）
- [x] 已建立独立集成分支 `integration/stage3e4` 并准备 PR 对比说明