@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "MODEL="
if exist ".config" (
    for /f "tokens=1* delims==" %%A in (.config) do (
        if "%%A"=="MODEL" set "MODEL=%%B"
    )
)

if "!MODEL!"=="" (
    call :ask_model
)

set "last_name="

:loop
cls
echo Current Model: !MODEL!
echo Commands: !q (quit), !m (change model), !u (update)
echo Enter your filename to compile:
set /p name=

if "!name!"=="" (
    if not "!last_name!"=="" (
        set "name=!last_name!"
        echo Using previous filename: !name!
    )
)
if /i "!name!"=="!q" exit /b 0
if /i "!name!"=="!m" (
    call :ask_model
    goto :loop
)
if /i "!name!"=="!u" (
    python lib\check_update.py
    pause
    goto :loop
)

set "last_name=!name!"

cls
echo Compiling: !name!...
python rac.py !MODEL! "!name!"

echo.
echo ===================================================
echo Done! Press any key to try another file...
pause > nul
goto :loop

:ask_model
set /p MODEL="Enter the model name you want to use (e.g. 580vnx, 880btg): "
if not exist "!MODEL!\" (
    echo Model directory '!MODEL!' does not exist! Please try again.
    goto ask_model
)
echo MODEL=!MODEL!> .config
exit /b 0
