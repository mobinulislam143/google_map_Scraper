@echo off
title Property Management Scraper
cls

echo ============================================================
echo GOOGLE MAPS PROPERTY MANAGEMENT SCRAPER
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1] Installing dependencies...
pip install -r requirements.txt -q

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [2] Starting scraper...
echo.

python scraper.py

pause
