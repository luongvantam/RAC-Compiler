@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
python -c "import textual" 2>nul
if errorlevel 1 (
    echo [RSC IDE] The 'textual' module is required. Installing from requirements.txt...
    echo [RSC IDE] Yêu cầu module 'textual'. Đang cài đặt từ requirements.txt...
    echo [RSC IDE] 需要 'textual' 模块。正在从 requirements.txt 安装...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [RSC IDE] Failed to install dependencies. Please install manually: python -m pip install -r requirements.txt
        echo [RSC IDE] Cài đặt thất bại. Vui lòng cài thủ công: python -m pip install -r requirements.txt
        echo [RSC IDE] 安装依赖失败。请手动安装: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)
:run_ide
python tui-ide\app.py
if %errorlevel% equ 3 (
    echo [RSC IDE] Restarting... / Đang khởi động lại... / 正在重启...
    goto run_ide
)
