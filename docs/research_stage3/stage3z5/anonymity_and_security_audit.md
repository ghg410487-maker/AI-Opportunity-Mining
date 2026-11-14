# 匿名与安全审查报告

- 日期：2026-11-14
- 扫描工具：`scripts/security_gate.py`
- 扫描目标：`competition_submission/`
- 扫描结果：32 个文件；HIGH=0，MEDIUM=1；`passed=true`，EXIT=0
- 报告：`logs/` 同级运行产物（正文不含密钥）

## 1. 扫描范围与规则

| 规则 | 内容 |
|---|---|
| 敏感文件 | `.env*`、`.pem`、`.key`、`id_rsa`、`credentials.json`、`.sqlite/.db` |
| 密钥模式 | `sk-*`、AWS Access Key、PRIVATE KEY 块、api_key/secret/token/password 赋值 |
| 私有路径 | `C:\Users\*`、`/home/*`、本机项目盘符路径、本机 Windows 用户名 |
| 匿名信息 | 团队称呼、文档 Author 元数据 |
| 受控材料 | `locked_evaluation`、`blinded`、`private_handoff`、`audit_package`、`guo_handoff` |
| 大文件 | 单文件 > 10 MB |

日志中的命中片段只保留前 4 个字符 + `***`，不输出密钥全文。

## 2. 结果

| severity | 数量 | 说明 |
|---|---:|---|
| HIGH | 0 | 无密钥、无私有路径、无敏感文件、无受控材料、无超大文件 |
| MEDIUM | 1 | `results/result1.csv` 第 1456 行匹配到 `Author:`，属于公开来源正文中的正常作者署名，不是本机个人信息；保留以免误删研究来源 |

## 3. 已完成的脱敏修复

1. 删除含真实 API Key 的 `.env`，保留 `.env.example`；
2. 修复 `.gitignore` 冲突标记，加入 `.env`、`.venv`、`__pycache__`、`data/`、大文件规则；
3. 页面不再显示 `E:\...` / `C:\Users\...` 绝对路径，改为相对路径；
4. 重新生成 4 张截图，扫描确认无绝对路径与用户名；
5. `cloudflared.exe` 与审计 zip 移入 `.local_materials/`，不进入提交包；
6. 提交包只包含公开 README、环境说明、切换摘要、演示指南、AI 使用模板、最小源码、四份结果和截图。

## 4. 内部文件与公开文件分层

- **公开提交包**：`competition_submission/`，不含内部验收报告、人工审核原件、私有评测集、绝对路径；
- **内部研发材料**：`docs/research_stage3/`、`experiments/`，保留真实路径、实验记录和人工审计数据，不随提交包发布；
- `competition_submission/docs/AI_usage_log.md` 是记录模板，不含真实姓名或密钥。

## 5. 剩余风险

| 风险 | 级别 | 处理建议 |
|---|---|---|
| 论文作者、学校、指导教师信息未匿名 | 中 | 论文定稿后单独做匿名版，不进本工程包 |
| Git 历史中存在 `.wbapp`、`.workbuddy` 工具元数据 | 低 | 当前不泄露密钥；如需彻底清理，另行重写历史，需负责人批准 |
| Streamlit 无鉴权 | 中 | 仅本地运行；公网部署前必须加反代、认证和访问控制 |
| 截图含系统界面信息 | 低 | 已确认无账号、无绝对路径；最终提交前再人工复核一次 |
| result1 正文含第三方作者署名 | 低 | 属合法引用，不删除；若官方匿名要求覆盖正文，需逐条审查 |

## 6. 结论

当前提交包 **未发现密钥、私有路径或受控材料泄漏**。可以进入正式候选材料评审；论文匿名、公网鉴权与 Git 历史清理需在负责人批准后另行处理。