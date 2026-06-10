@echo off
cd /d "%~dp0"
venv\Scripts\python.exe web_app.py --host 0.0.0.0 --port 8000
if %errorlevel% neq 0 (
    echo [오류] web_app.py 실행 실패. exit code: %errorlevel%
    pause
)
