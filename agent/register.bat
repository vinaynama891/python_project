@echo off
title CloudPulse Agent Register
cd /d "%~dp0"

echo =======================================================
echo          CloudPulse Agent Quick Registration          
echo =======================================================
echo.

set /p TOKEN="Enter Registration Token (e.g. cp_reg_...): "
if "%TOKEN%"=="" (
    echo Error: Token cannot be empty!
    pause
    exit /b 1
)

set /p NAME="Enter Server Name (e.g. tanish_laptop): "
if "%NAME%"=="" (
    set NAME=tanish_laptop
)

set /p SERVER_IP="Enter Host IP [Press Enter for default: 10.174.8.80]: "
if "%SERVER_IP%"=="" (
    set SERVER_IP=10.174.8.80
)

echo.
echo Installing dependencies if needed...
pip install psutil requests

echo.
echo Registering with CloudPulse Backend at http://%SERVER_IP%:8000 ...
python main.py --register %TOKEN% --url http://%SERVER_IP%:8000 --name "%NAME%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Registration failed! Please verify token and check that Host IP is reachable.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo Registration Successful! Starting Agent Monitoring...
echo =======================================================
echo.
python main.py
pause
