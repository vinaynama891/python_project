@echo off
title CloudPulse Monitoring Agent
cd /d "%~dp0"

echo =======================================================
echo          CloudPulse Agent Real-Time Monitor            
echo =======================================================
echo.

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Agent exited with error.
    pause
)
