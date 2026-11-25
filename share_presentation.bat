@echo off
title Group 6 AI Web Agent - Public Presentation Host
cls
echo ==================================================================
echo   🌟 Group 6 AI Project - Secure Presentation Link Generator
echo ==================================================================
echo.

if not exist "bin\cloudflared.exe" (
    echo [*] Cloudflare Tunnel binary not found. Downloading...
    if not exist "bin" mkdir bin
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'bin\cloudflared.exe'"
    echo [OK] Cloudflare Tunnel downloaded successfully.
    echo.
)

:: Check if server is running on port 8000
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Agent server is not running on port 8000.
    echo [*] Starting web server in a separate window...
    start "Group 6 Agent Server" cmd /k ".\start_web.bat"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Local agent server is active on port 8000.
)

echo.
echo ==================================================================
echo   🚀 Launching Secure Cloudflare HTTPS Tunnel...
echo   Look for your public link below (e.g. https://xxxx.trycloudflare.com)
echo   Share that link with your audience or open it on your phone!
echo   (Press Ctrl+C anytime to stop sharing)
echo ==================================================================
echo.

bin\cloudflared.exe tunnel --url http://127.0.0.1:8000
pause
