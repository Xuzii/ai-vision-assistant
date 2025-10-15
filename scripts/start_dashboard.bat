@echo off
REM Quick Start Script for Life Tracking Dashboard
REM Windows version

echo ============================================================
echo    Life Tracking Dashboard - Starting...
echo ============================================================
echo.

REM Check if database exists
if not exist activities.db (
    echo Setting up database for first time...
    python database_setup.py
    echo.
    echo ⚠️  SAVE THE PASSWORD SHOWN ABOVE!
    echo.
    pause
)

echo Starting dashboard server...
echo.
echo 🌐 Dashboard will be available at:
echo    http://localhost:8000
echo.
echo 🔐 Login with your credentials
echo.
echo Press Ctrl+C to stop
echo.

python dashboard.py

pause
