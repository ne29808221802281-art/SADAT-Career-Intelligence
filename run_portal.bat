@echo off
title SADAT Career Intelligence & Skills Growth Portal
echo ========================================================
echo  SADAT - Student Career Intelligence Portal
echo  Faculty of Computers and Information - Class of 2026
echo ========================================================
echo.

set PYTHON_CMD="C:\Users\elmasria\AppData\Local\Programs\Orange\python.exe"
set NODE_CMD="C:\Users\elmasria\AppData\Roaming\Antigravity\bin\agy-node.cmd"

echo [1/3] Starting Private Python Intelligence Service on port 8000...
start "SADAT Intelligence Service" /B %PYTHON_CMD% services\intelligence\server.py 8000

echo [2/3] Starting Standalone Node.js REST API Server on port 5000...
start "SADAT API Server" /B %NODE_CMD% apps\api\src\server.js

echo [3/3] Launching Web Portal in your default browser...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000

echo.
echo Portal is active and running!
echo Access URL: http://127.0.0.1:5000
echo Offline Direct File: apps\web\public\index.html
echo Press any key to stop all background services.
pause >nul

taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM Antigravity.exe /T 2>nul
