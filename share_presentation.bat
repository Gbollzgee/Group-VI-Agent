@echo off
title Group 6 AI Web Agent - Public Presentation Host
cd /d "%~dp0"
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

:: Strictly check if port 8000 is in LISTENING state
netstat -ano -p tcp | findstr /R /C:" 127\.0\.0\.1:8000 .*LISTENING" /C:" 0\.0\.0\.0:8000 .*LISTENING" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Web agent server is not active on port 8000.
    echo [*] Starting web agent server in a dedicated window...
    start "Group 6 Agent Server" cmd /k "cd /d ""%~dp0"" && start_web.bat"
    
    echo [*] Waiting for server on port 8000 to become ready...
    :wait_server
    timeout /t 2 /nobreak >nul
    netstat -ano -p tcp | findstr /R /C:" 127\.0\.0\.1:8000 .*LISTENING" /C:" 0\.0\.0\.0:8000 .*LISTENING" >nul
    if %ERRORLEVEL% NEQ 0 (
        echo [*] Server is booting up... please hold on...
        goto wait_server
    )
    echo [OK] Web agent server is online and listening on port 8000!
) else (
    echo [OK] Local agent server is already verified active on port 8000.
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
