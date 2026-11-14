# 环境与部署说明

## 环境

- Python 3.11+（验证版本 3.12）
- Windows 11 / Linux / macOS
- 依赖：streamlit、pandas、requests、beautifulsoup4、pytest

## 安装

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # Windows
.venv/bin/python -m pip install -r requirements.txt       # Linux/macOS
```

## 启动

```bash
run_system.bat   # Windows
bash run_system.sh
# 或
streamlit run app.py
```

## 部署边界

当前交付为本地运行模式，不包含长期稳定公网入口。若需公网演示，应由负责人评估并批准反代、认证和费用，不得擅自创建付费资源。

## 数据依赖

- `results/result1.csv` 必须有数据；
- `result3.csv`、`result4.csv` 用于主题与评分页面；
- 数据缺失时页面显示提示，不崩溃；
- 密钥只从本地 `.env` 读取，提交包不包含 `.env`。
