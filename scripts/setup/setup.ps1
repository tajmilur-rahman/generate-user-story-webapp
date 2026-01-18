# Automated Setup Script for User Story Automation (PowerShell)
# This script installs all required dependencies for the project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "User Story Automation - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if pip is available
Write-Host "[2/6] Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = python -m pip --version 2>&1
    Write-Host "✓ pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "Installing pip..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
}
Write-Host ""

# Create virtual environment
Write-Host "[3/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists. Skipping..." -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created!" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment and upgrade pip
Write-Host "[4/6] Activating virtual environment and upgrading pip..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
Write-Host "✓ pip upgraded!" -ForegroundColor Green
Write-Host ""

# Install Python dependencies
Write-Host "[5/6] Installing Python dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✓ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "✗ WARNING: requirements.txt not found!" -ForegroundColor Red
}
Write-Host ""

# Create .env file from template
Write-Host "[6/6] Setting up environment file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists. Skipping..." -ForegroundColor Green
} else {
    if (Test-Path "config\env.template") {
        Copy-Item "config\env.template" ".env"
        Write-Host "✓ .env file created from template!" -ForegroundColor Green
        Write-Host "Please edit .env file with your configuration." -ForegroundColor Yellow
    } else {
        Write-Host "✗ WARNING: config\env.template not found!" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Install Ollama from: https://ollama.ai/download" -ForegroundColor White
Write-Host "3. Run: ollama pull llama3.2" -ForegroundColor White
Write-Host "4. Activate virtual environment: venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "5. Run application: python run.py" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see docs/README.md" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

