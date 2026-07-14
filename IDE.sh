#!/bin/bash
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then
    PY="python3"
elif command -v python &> /dev/null; then
    PY="python"
else
    echo "[RSC IDE] Python is not installed or not in PATH."
    echo "[RSC IDE] Python chưa được cài đặt hoặc không có trong PATH."
    echo "[RSC IDE] 未安装 Python 或未加入 PATH。"
    exit 1
fi

if ! $PY -c "import textual" &> /dev/null; then
    echo "[RSC IDE] The 'textual' module is required. Installing from requirements.txt..."
    echo "[RSC IDE] Yêu cầu module 'textual'. Đang cài đặt từ requirements.txt..."
    echo "[RSC IDE] 需要 'textual' 模块。正在从 requirements.txt 安装..."
    $PY -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[RSC IDE] Failed to install dependencies. Please install manually: $PY -m pip install -r requirements.txt"
        echo "[RSC IDE] Cài đặt thất bại. Vui lòng cài thủ công: $PY -m pip install -r requirements.txt"
        echo "[RSC IDE] 安装依赖失败。请手动安装: $PY -m pip install -r requirements.txt"
        exit 1
    fi
fi

while true; do
    $PY tui-ide/app.py
    if [ $? -ne 3 ]; then
        break
    fi
    echo "[RSC IDE] Restarting... / Đang khởi động lại... / 正在重启..."
done
