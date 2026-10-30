@echo off
title J.A.R.V.I.S. MARK VII - Neural AI Assistant
color 0b
echo ========================================================
echo        J.A.R.V.I.S. // MARK VII TACTICAL AI CORE        
echo               Supabase Cloud Backend Active             
echo ========================================================
echo.
echo [1/2] Initializing Core Neural Interfaces...

:: Launch browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

echo [2/2] Starting Tactical Server on http://127.0.0.1:8000
python server.py
pause
