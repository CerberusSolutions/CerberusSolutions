@echo off
REM Windows launcher for rttview. Double-click or: run.bat [folder-of-RTT-files]
setlocal
set TARGET=%~1
if "%TARGET%"=="" set TARGET=samples

REM Ensure the curses backend exists on Windows; install it if missing.
python -c "import curses" 1>/dev/null 2>/dev/null
if errorlevel 1 (
  echo Installing windows-curses ...
  python -m pip install windows-curses
)

python -m rttview "%TARGET%"
endlocal
