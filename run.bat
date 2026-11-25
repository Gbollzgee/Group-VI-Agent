@echo off
title Group 6 AI Project - Web Agent
cd /d "%~dp0"

echo ========================================================
echo         Group 6 AI Project - Web Agent Launcher
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please make sure the dependencies are installed.
    pause
    exit /b 1
)

echo Starting agent...
echo.
".venv\Scripts\python.exe" main.py

echo.
echo ========================================================
echo Execution completed.
pause
