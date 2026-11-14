#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUTF8=1

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
else
  PY="${PYTHON:-python3}"
fi

if ! "$PY" -c "import streamlit, pandas" >/dev/null 2>&1; then
  echo "[AIjiaoyu] 正在安装依赖..."
  "$PY" -m pip install -r requirements.txt
fi

echo "[AIjiaoyu] 启动系统：http://localhost:8501"
exec "$PY" -m streamlit run app.py