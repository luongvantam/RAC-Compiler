:main
@echo off
cls
cd /d "%~dp0"
set /p name="Enter your filename to compile (for 580VNX only) or type "0" to exit: "
if "%name%"=="0" (
    echo Script aborted.
    exit /b
)
cls 
python rac.py 580vnx ./rsc_ropchain/%name%
echo.
echo Press any key to go back...
pause >nul 2>&1
goto main