@echo off
REM CV Alarm Client Startup Script for Windows
REM This script starts the alarm client with proper paths

REM Change to the alarm_client directory
cd /d "%~dp0\.."

REM Activate virtual environment and run
call venv\Scripts\activate.bat
python main.py

REM If python exits, pause to see any error messages
pause
