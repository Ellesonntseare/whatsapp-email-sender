@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 start.py
    goto done
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    python start.py
    goto done
)
echo Python 3 is needed to run localhost. You can open index.html directly to play offline.
:done
pause
