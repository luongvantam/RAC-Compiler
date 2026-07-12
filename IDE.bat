@echo off
cd /d "%~dp0"
python -c "import textual" 2>nul
if errorlevel 1 (
    echo [RSC IDE] The 'textual' module is required. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [RSC IDE] Failed to install dependencies. Please install manually: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)
:run_ide
python lib\ide.py
if %errorlevel% equ 3 (
    echo [RSC IDE] Restarting...
    goto run_ide
)
