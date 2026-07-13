#!/bin/bash
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then
    PY="python3"
elif command -v python &> /dev/null; then
    PY="python"
else
    echo "[RSC IDE] Python is not installed or not in PATH."
    exit 1
fi

if ! $PY -c "import textual" &> /dev/null; then
    echo "[RSC IDE] The 'textual' module is required. Installing from requirements.txt..."
    $PY -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[RSC IDE] Failed to install dependencies. Please install manually: $PY -m pip install -r requirements.txt"
        exit 1
    fi
fi

while true; do
    $PY tui-ide/app.py
    if [ $? -ne 3 ]; then
        break
    fi
    echo "[RSC IDE] Restarting..."
done
