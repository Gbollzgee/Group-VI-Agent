@echo off
title Group 6 AI Project - Web Agent & Voice Interface
cd /d "%~dp0"

echo ========================================================
echo   Group 6 AI Project - Web & Voice Agent Launcher
echo   Topic: Goal-Oriented AI Web Agent for Navigation
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv.
    pause
    exit /b 1
)

echo Starting Web Agent Server on port 8000...
echo Opening browser at http://localhost:8000
echo.

:: Launch browser in background after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start the aiohttp server
".venv\Scripts\python.exe" web\server.py

echo.
echo Server stopped.
pause
