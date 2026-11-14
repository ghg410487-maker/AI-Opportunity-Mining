# Z5-1 干净环境复现验收

- 日期：2026-11-14
- 结论：**Windows 干净环境复现成功**；Mac/Linux 仅完成静态验证，未做实机验收。
- 独立目录：`E:/AIjiaoyu_z5_clean`（不属于原工作区，未复用原 `.venv`、`__pycache__` 或本地缓存）
- 源码来源：本地 Git 仓库 `integration/stage3e4` 的 `git clone --no-local`（隔离未跟踪文件）
- 日志：`logs/01_clean_setup.log`、`logs/02_pytest_clean.log`、`logs/03_validate_preview.log`、`logs/03_validate_strict.log`、`logs/04_startup_restart.log`、`logs/05_page_and_missing_data.log`

## 1. 环境

| 项目 | 值 |
|---|---|
| Python | 3.12.0 |
| 平台 | Windows-11-10.0.26200-SP0 |
| 虚拟环境 | 全新 `.venv`（`python -m venv`） |
| 依赖安装 | `pip install -r requirements.txt`，成功 |
| 关键版本 | streamlit 1.67.0 / pandas 3.1.1 / beautifulsoup4 4.15.0 / requests 2.34.2 / pytest 9.2.0 |

## 2. 复现命令

```bash
git clone --no-local -b integration/stage3e4 E:/AIjiaoyu E:/AIjiaoyu_z5_clean
cd E:/AIjiaoyu_z5_clean
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

按 README 准备受控数据到 `results/final/`：

- `result1_Final_All.csv`
- `result2_resolved_subset.csv`
- `result2_export_blockers.csv`
- `result3.csv`、`result4.csv`
- `unified_records.jsonl`
- `experiments/stage3e3/cluster5_guo_initial_audit.csv`（人工审计旁路；缺失时应用回退到 C004 默认暂停，不崩溃）

## 3. 实测结果

| 检查 | 命令 | 结果 |
|---|---|---|
| 测试 | `.venv/Scripts/python.exe -m pytest -q` | **35 passed** |
| 预览校验 | `python scripts/validate_csv.py` | EXIT=0，部分通过 |
| 严格校验 | `python scripts/validate_csv.py --strict` | **NOT_READY，EXIT=1**（595 REVIEW） |
| 首次启动 | `run_system.bat` | HTTP 200，5.8 秒 |
| 重启 | 停止后再次 `run_system.bat` | HTTP 200，6.7 秒 |
| 页面行为 | Playwright 访问主题/排行/策划案 | C004 提示、人工分层、下载按钮均存在；无绝对路径 |
| 缺 result3 | 临时移走 `result3.csv`，切到主题页 | 无异常，显示“待算法端输出”与 Mock 标注 |
| 缺 result4 | 临时移走 `result4.csv`，切到排行页 | 无异常，显示“待算法端输出”与 Mock 标注 |

## 4. 路径依赖核查

- 不依赖个人用户名：页面文本检查未出现 `C:\Users/*`、`86136`、`/home/*`。
- 不依赖固定盘符：`app.py` 先使用 `BASE_DIR/results`，不存在时回退到 `BASE_DIR.parent/results`，同时兼容 `results/final/*` 与官方 `results/result*.csv`。
- 不依赖 Codex/IDE 缓存：干净目录不含 `.codeartsdoer/`、`.venv/`、`__pycache__/`。
- 受控数据缺失时：主数据缺失显示“当前没有可用记录”，result3/4 缺失显示提示 + Mock 标注，不崩溃。
- 额外依赖：`experiments/stage3e3/cluster5_guo_initial_audit.csv` 只影响 C004 动态识别与人工分层展示；缺失时回退到固定 C004 暂停列表。

## 5. Mac/Linux 静态验证

```bash
bash -n run_system.sh      # 语法检查通过
ls -l run_system.sh        # 可执行权限存在
```

脚本支持 `.venv/bin/python`、`.venv/Scripts/python.exe` 与 `python3` 三种解释器路径。未在真实 macOS/Linux 主机运行，不能声称已完成实机验收。

## 6. 偏差与限制

- `git fetch origin` 失败：`github.com:443` 经本地代理不可达，无法确认远程最新 dev。
- `integration/stage3e4` 未 push 到远端，因此“从远程集成分支获取源码”退化为“从本地已冻结提交 clone 的独立工作区”，源码与提交对象一致，但不满足远程拉取。
- 干净环境使用受控数据复制（数据本身不入 Git），这是 README 允许的数据准备步骤。