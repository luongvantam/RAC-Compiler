@echo off

set "last_name="

:loop
cls
echo Enter your filename to compile (for 580VNX only):
set /p name=

if "%name%"=="" (
    if not "%last_name%"=="" (
        set "name=%last_name%"
        echo Using previous filename: %name%
    )
)

set "last_name=%name%"

cls
echo Compiling: %name%...
python lib\main.py 580vnx "%name%"

echo.
echo ===================================================
echo Done! Press any key to try another file...
pause > nul
goto :loop