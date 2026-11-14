# Stage 3Z-5 正式提交工程总验收报告

- 日期：2026-11-14
- 工程基线：`integration/stage3e4`
- 算法基线：`origin/dev@bab6db8`（远程不可达，未确认是否有更新）
- 数据口径：**v1 实验数据（42 机会 / 595 REVIEW）**，未混入 v2（16 机会 / 601 REVIEW）
- 总体结论：**工程可独立复现、可校验、可安全切换、可生成提交骨架；正式提交仍被 result2 的 REVIEW 政策阻断。**

## 一、12 个必答问题

### 1. 能否在独立干净环境重新启动？

**能（Windows 实测）。**

- 独立目录 `E:/AIjiaoyu_z5_clean`，全新 `.venv`，不复用原环境；
- Python 3.12.0 / Windows-11-10.0.26200；
- `pip install -r requirements.txt` 成功；
- pytest 35 passed；首次启动 HTTP 200（5.8s），重启 HTTP 200（6.7s）；
- 证据：`clean_environment_reproduction.md`、`logs/01..05`。

限制：GitHub 不可达，源码来自本地 `git clone --no-local` 的冻结提交；Mac/Linux 仅静态验证。

### 2. 官方提交包除正式算法结果还缺什么？

- 论文 Word/PDF；
- 真实 AI 使用记录（当前仅模板）；
- 附件1标签映射的最终核验；
- 稳定公网部署与访问说明（如需）；
- 负责人 REVIEW 政策审批。

证据：`submission_package_audit.md`、`competition_submission/submission_checklist.md`。

### 3. 当前是否存在占位文件误提交风险？

**存在 result2 0 行占位，但已被三层闸门阻断。**

- `build_submission.py --release` → `RELEASE_BLOCKED`，EXIT=1；
- `validate_csv.py --strict --results-dir competition_submission/results` → `NOT_READY`，EXIT=1；
- `switch_official_results.py` → `submission_ready=false` 时 `BLOCKED_MANIFEST`；
- manifest 将 result2 标记 `formal=false`、`status=NOT_READY`。

### 4. 正式结果切换能否自动完成？

**能，但必须审批通过且停止服务。**

- 脚本：`scripts/switch_official_results.py`；
- 覆盖正常切换、缺失文件、REVIEW、非机会 ID、簇不一致、哈希不符、审批缺失、服务运行、切换失败、回滚共 10 个场景；
- 测试 10 passed，日志 `logs/06_switch_dry_run.log`；
- 失败自动回滚，证据：`switch_dry_run_report.md`。

### 5. 严格校验是否正确阻断错误输入？

**是。**

- 当前 595 REVIEW → `NOT_READY` + EXIT=1；
- 缺失 result1/result2、result2 非 0/1、result3 引用非机会 ID、result4 簇集合不一致、哈希不符均被阻断；
- 预览模式仍为 EXIT=0，严格模式为 EXIT=1。

### 6. 人工结果与机器结果能否清晰区分？

**能。**

- 主题页新增“人工审核分层”，独立展示机器记录数、人工确认、人工否定、证据不足、人工支持状态、负责人裁决；
- 机器五簇仍作为算法实验展示；
- C004 在推荐视图暂停；C003/C004 明确不进入“已确认高价值推荐”；
- 未把人工 12 条正例塞回机器五簇；
- 加权 Precision/Recall/F1 等指标在缺少真实评估文件时只显示等待提示，不填数字。

### 7. 是否存在匿名和密钥泄漏风险？

**提交包未发现密钥或私有路径。**

- 安全门禁 32 个文件，HIGH=0，MEDIUM=1（result1 正文中的 `Author:` 正常署名）；
- `.env` 已删除，保留脱敏 `.env.example`；
- 页面与截图已去除绝对路径和本机用户名；
- 剩余风险：论文匿名版、Streamlit 公网鉴权、Git 历史工具元数据。
- 证据：`anonymity_and_security_audit.md`。

### 8. 实际部署属于本地、临时隧道还是稳定公网？

**本地运行。**

- 无 Cloudflare 隧道运行；`cloudflared.exe` 已隔离；
- 无云主机、域名、反代、认证；
- 未创建付费资源；
- 证据：`deployment_stability_report.md`。

### 9. 5 分钟演示能否完整走通？

**能走通 8 步流程。**

- 数据概览、机会状态、机器聚类、价值排行、人工审计、策划案、下载均可用；
- 但第 1 步只支持预置数据，不触发实时采集；策划案为本地模板生成，不是实时 LLM；演示必须如实说明；
- 证据：`demo_guide_final_candidate.md` 与 4 张截图。

### 10. main、dev 和 integration 合并是否存在冲突？

**当前无真实冲突。**

- `origin/dev@bab6db8` → `origin/main@d73ac6d` → `integration/stage3e4@b22600d` 为线性包含；
- `git merge-tree` 无冲突标记；输出中的 `ON CONFLICT` 是 SQL 文本；
- 但远程不可达，合并前必须重新 fetch，防止 dev 已前进。
- 证据：`branch_merge_plan.md`。

### 11. 哪些事项必须等待负责人审批？

- 601/595 REVIEW 的最终处置政策；
- 正式算法版本、算法配置版本、标签映射版本；
- `submission_ready=true` 的审批标志；
- 是否将集成分支 push 到远端并创建 PR；
- 是否部署稳定公网入口及相应费用；
- 论文匿名版与最终官方材料清单。

### 12. 最终提交前还有什么风险？

| 风险 | 级别 | 说明 |
|---|---|---|
| result2 仍为 0 行占位 | 高 | 正式提交被阻断 |
| 算法 v2 未冻结 | 高 | 切换后需整包重算，禁止 v1/v2 混装 |
| 论文/AI 使用记录缺失 | 高 | 官方材料不完整 |
| 远程不可达、集成分支未 push | 中 | 评审无法拉取，合并前需恢复网络 |
| 公网部署与鉴权缺失 | 中 | 仅适合本地演示 |
| Git 历史工具元数据 | 低 | 不泄露密钥，必要时另行清理 |
| 截图最终人工复核 | 低 | 当前扫描无路径/账号 |

## 二、本轮交付物

```text
docs/research_stage3/stage3z5/
├── clean_environment_reproduction.md
├── submission_package_audit.md
├── submission_manifest.json
├── official_result_switch_contract.md
├── switch_dry_run_report.md
├── anonymity_and_security_audit.md
├── demo_guide_final_candidate.md
├── deployment_stability_report.md
├── branch_merge_plan.md
├── stage3z5_acceptance_report.md
└── logs/
    ├── 01_clean_setup.log
    ├── 02_pytest_clean.log
    ├── 03_validate_preview.log
    ├── 03_validate_strict.log
    ├── 04_startup_restart.log
    ├── 05_page_and_missing_data.log
    └── 06_switch_dry_run.log
```

新增/更新的工程文件：

- `scripts/switch_official_results.py`：原子切换与回滚；
- `scripts/security_gate.py`：发布前安全门禁；
- `scripts/build_submission.py`：提交包构建、manifest、release 阻断；
- `scripts/validate_csv.py`：支持 `--results-dir` 与官方全量 result2；
- `tests/test_switch_official_results.py`：10 个切换场景；
- `app.py`：人工审核分层、C003/C004 提示、相对路径、提交包数据根回退；
- `config/official_headers.py`：result3 表头对齐官方模板；
- `competition_submission/`：results/source/docs/screenshots/manifest/checklist。

## 三、测试汇总

```text
主工作区：35 passed
干净环境：35 passed
严格校验：NOT_READY，EXIT=1（595 REVIEW）
预览校验：EXIT=0
release 构建：RELEASE_BLOCKED，EXIT=1
安全门禁：HIGH=0，MEDIUM=1，EXIT=0
干净环境启动：HTTP 200，5.8s
干净环境重启：HTTP 200，6.7s
切换预演：10 passed
```

## 四、完成标准核对

- [x] 独立干净环境安装、启动、测试、重启；
- [x] 提交包结构规范、manifest 与哈希；
- [x] 正式 CSV 导出联动契约与原子切换；
- [x] 合成数据 10 场景预演与回滚；
- [x] 人工审核与机器结果分层展示；
- [x] 匿名、密钥、路径、大文件安全门禁；
- [x] 分支差异与合并计划；
- [x] 严格校验与 release 阻断；
- [ ] result2 全量正式结果（等待 REVIEW 审批）；
- [ ] 论文、AI 使用记录与最终官方材料（等待团队）。

**结论：工程侧已具备独立复现、安全切换、严格校验和正式提交能力；正式发布仍需负责人审批与正式算法结果。**