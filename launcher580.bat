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

set "filepath=.\rsc_ropchain\%name%"

if exist "%filepath%" (
    goto :found
)

if exist "%filepath%.rsc" (
    set "name=%name%.rsc"
    goto :found
)

cls
echo Error: File "%name%" or "%name%.rsc" not found in .\rsc_ropchain\
echo Please double-check the filename.
echo.
pause
goto :loop

:found
set "last_name=%name%"

cls
echo Compiling: %name%...
python run.py 580vnx ".\rsc_ropchain\%name%"

echo.
echo ===================================================
echo Done! Press any key to try another file...
pause > nul
goto :loop