# Property Management Scraper - PowerShell Runner
$Host.UI.RawUI.WindowTitle = "Property Management Scraper"
Clear-Host

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "GOOGLE MAPS PROPERTY MANAGEMENT SCRAPER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[1] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "[2] Starting scraper..." -ForegroundColor Yellow
Write-Host ""

python scraper.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Script finished. Press Enter to exit." -ForegroundColor Cyan
Read-Host
