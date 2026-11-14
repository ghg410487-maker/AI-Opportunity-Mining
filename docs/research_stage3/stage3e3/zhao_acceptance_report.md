# 赵的 Web 系统集成验收报告（Stage 3E-3）

- 验收日期：2026-11-14
- 拉取基线：`origin/dev` commit `bab6db8`（fix(stage3e3): skip private handoff check in public clone）
- 本地合并提交：`c76c12e`（Merge remote-tracking branch 'origin/dev'）
- 运行环境：Python 3.12 / Streamlit 1.67 / pandas 3.1.1 / Windows
- 数据源：`results/final/result1_Final_All.csv`（1984 条）

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

重写为四份官方 CSV 核对脚本：

- result1：行数、记录编号唯一性；
- result2：已决子集 + REVIEW 阻断表，记录编号唯一、状态仅 0/1、两表无重叠、与 result1 全量对账；
- result3：主题簇编号唯一、簇内记录无重复、与 result2 机会=1 记录对账；
- result4：主题簇编号唯一、与 result3 簇集合与行数一致、分数范围 0-100、优先级唯一；
- REVIEW 存在时输出“部分通过 / 待 REVIEW 审批”，退出码为 0，不崩溃、不做映射。

## 2. 校验日志

```text
=== 官方四份 CSV 核对 ===
目录：E:\AIjiaoyu\results\final
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

说明：当前 `result2_export_blockers.csv` 实际为 595 条；Stage 3E-3 的 `review601_disposition_queue.csv` 为 601 条待处置队列，两者口径不同。校验脚本按实际文件动态统计，601/595 均保持 REVIEW 阻断，未映射为 0 或 1。

## 3. 页面测试日志

```text
[数据概览]     exceptions=0  warnings=0  C004提示=False  下载按钮=0
[机会主题发现] exceptions=0  warnings=1  C004提示=True   表格行数=4
[机会价值排行] exceptions=0  warnings=1  C004提示=True   表格行数=4
[机会策划案]   exceptions=0  warnings=1  C004提示=True   下载按钮=1
```

- AppTest 四个页面均无异常；
- 主题发现与排行均只展示 4 个簇（C002/C005/C001/C003），C004 被过滤；
- 策划案主题选项不含 C004，下载按钮可用（`disabled=False`）；
- `streamlit run app.py` 启动成功，HTTP 200；
- `pytest`：24 passed，1 failed；唯一失败为既有基线问题 `tests/test_headers.py`（缺少 `results/B01/result1.csv`），与本次改动无关。

## 4. 关键页面截图

| 页面 | 截图路径 |
|---|---|
| 数据概览 | `docs/research_stage3/stage3e3/screenshots/overview.png` |
| 机会主题发现（C004 已暂停） | `docs/research_stage3/stage3e3/screenshots/topics.png` |
| 机会价值排行（C004 已暂停） | `docs/research_stage3/stage3e3/screenshots/ranking.png` |
| 机会策划案（含下载按钮） | `docs/research_stage3/stage3e3/screenshots/plan.png` |

截图由 Playwright + 本机 Chrome 在 1500×1200 视口下自动生成，均为真实运行页面。

## 5. 当前系统文件保存路径

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
| 本验收报告 | `docs/research_stage3/stage3e3/zhao_acceptance_report.md` |

## 6. 约束确认

- [x] 已拉取并合并 `origin/dev` 最新提交 `bab6db8`
- [x] 使用真实 `result3.csv`、`result4.csv`，未删除、未替换 Mock
- [x] C004 人工全否簇已从推荐视图过滤，并保留说明
- [x] 页面顶部保留实验候选、非正式提交版警告
- [x] 595/601 条 REVIEW 均未映射为 0 或 1
- [x] 策划案支持下载 Markdown
- [x] 四份 CSV 校验脚本支持部分通过与待 REVIEW 审批提示