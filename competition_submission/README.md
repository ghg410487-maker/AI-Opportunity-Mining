# 教育 AI 应用场景智能挖掘与机会评估系统

本提交包是第三届甘肃省大学生数据挖掘挑战赛本科组赛题作品的可运行工程包。
系统围绕教育 AI 场景，展示多源数据清洗、机会判别、主题聚类、价值评分与策划案生成流程。

## 快速启动

```bash
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements.txt
run_system.bat

# Linux / macOS
.venv/bin/python -m pip install -r requirements.txt
bash run_system.sh
```

浏览器访问 <http://localhost:8501>。

## 数据与结果

- `results/result1.csv`：多源采集与清洗记录
- `results/result2.csv`：逐条机会判别（当前状态见 `submission_checklist.md`）
- `results/result3.csv`：主题聚类与簇内记录追溯
- `results/result4.csv`：机会价值评分与优先级
- `results/` 下文件名与官方四份 CSV 模板一致。

数据准备与重新生成：

```bash
python -m edumine competition-mvp --input results/result1.csv --output results
```

## 校验

```bash
python scripts/validate_csv.py --strict --results-dir results
```

正式提交前必须返回 `READY_FOR_SUBMISSION`，否则不得打包。

## 目录

```
competition_submission/
├── results/        # 官方四份 CSV
├── source/         # 最小可运行源码
├── docs/           # 启动、部署、切换、AI 使用说明
├── screenshots/    # 系统关键页面截图
├── README.md
├── submission_checklist.md
└── manifest.json
```

## 核心创新

1. 多源证据可追溯：每条机会记录保留来源与簇内记录编号；
2. 可解释价值评分：维度分数可独立重算，不依赖黑盒；
3. 人工审计旁路：机器结果与人工审核分层展示，不把人工结论伪装成新的机器聚类；
4. 正式结果原子切换：审批、哈希、严格校验和回滚形成完整发布闸门。

## 版本状态

本包版本与是否正式提交以 `manifest.json` 和 `submission_checklist.md` 为准。
当前若仍为 `NOT_READY`，表示 result2 的 REVIEW 政策尚未批准，禁止正式提交。
