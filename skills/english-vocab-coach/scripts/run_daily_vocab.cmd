@echo off
REM Wrapper for the daily English vocab routine (called by Windows Task Scheduler).
REM Sets UTF-8 so Vietnamese output survives, and ensures the npm global dir
REM (where `claude` lives) is on PATH for the claude -p call.
set PYTHONIOENCODING=utf-8
set "PATH=%PATH%;C:\Users\wi\AppData\Roaming\npm"
"C:\Python314\python.exe" "C:\Users\wi\.claude\skills\english-vocab-coach\scripts\daily_vocab.py" >> "d:\HK8\Learning\DQ\vocab\task_stdout.log" 2>&1
