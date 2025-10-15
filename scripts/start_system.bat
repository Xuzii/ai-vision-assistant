@echo off
REM Start Life Tracking System
REM Runs both Camera Manager and Dashboard simultaneously

set PYTHON=C:\Users\turd\AppData\Local\Programs\Python\Python311\python.exe

echo ============================================================
echo LIFE TRACKING SYSTEM - STARTUP
echo ============================================================
echo.
echo Starting services:
echo   1. Camera Manager (background tracking)
echo   2. Dashboard (web interface)
echo.
echo Dashboard will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop all services
echo ============================================================
echo.

REM Start camera manager in background
echo [1/2] Starting Camera Manager...
start "Camera Manager" /MIN %PYTHON% camera_manager.py

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start dashboard (this will keep the window open)
echo [2/2] Starting Dashboard...
echo.
%PYTHON% dashboard.py

REM If dashboard exits, this runs
echo.
echo Dashboard stopped. Press any key to exit...
pause >nul
