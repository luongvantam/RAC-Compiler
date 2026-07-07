@echo off

set "last_name="

:loop
cls
echo Enter your filename to compile (for 880BTG only):
set /p name=

if "%name%"=="" (
    if not "%last_name%"=="" (
        set "name=%last_name%"
        echo Using previous filename: %name%
    )
)

set "filepath=.\rsc_ropchain\%name%"
if exist "%filepath%" goto :run_python
if exist "%filepath%.rsc" set "name=%name%.rsc" & goto :run_python
if exist "%filepath%.asm" set "name=%name%.asm" & goto :run_python

set "filepath=.\asm_ropchain\%name%"
if exist "%filepath%" goto :run_python
if exist "%filepath%.rsc" set "name=%name%.rsc" & goto :run_python
if exist "%filepath%.asm" set "name=%name%.asm" & goto :run_python

cls
echo Error: File "%name%" not found in .\rsc_ropchain\ or .\asm_ropchain\
echo Please double-check the filename.
echo.
pause
goto :loop

:run_python
set "last_name=%name%"

cls
echo Compiling: %name%...
python lib\main.py 880btg "%name%"

echo.
echo ===================================================
echo Done! Press any key to try another file...
pause > nul
goto :loop