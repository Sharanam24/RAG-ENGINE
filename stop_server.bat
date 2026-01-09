@echo off
echo Stopping server on port 8000...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping process ID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo.
echo Server stopped. You can now run: python main.py
echo.
