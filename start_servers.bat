@echo off
echo =========================================================
echo Starting WorkforceHub Attendance System
echo =========================================================

start "WorkforceHub Backend (FastAPI)" cmd /k "cd /d %~dp0\backend && py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 >nul
start "WorkforceHub Frontend (Vite Web)" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Servers started:
echo - Backend API:  http://localhost:8000
echo - Swagger Docs: http://localhost:8000/docs
echo - Web App:      http://localhost:5173
echo.
pause
