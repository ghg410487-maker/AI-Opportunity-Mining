@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" -c "import streamlit, pandas" >nul 2>&1
if errorlevel 1 (
  echo [AIjiaoyu] 正在安装依赖...
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [AIjiaoyu] 依赖安装失败，请检查网络或 Python 环境。
    exit /b 1
  )
)

echo [AIjiaoyu] 启动系统：http://localhost:8501
"%PY%" -m streamlit run app.py