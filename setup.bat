@echo off
REM Automated Setup Script for User Story Automation
REM This script installs all required dependencies for the project

echo ========================================
echo User Story Automation - Setup Script
echo ========================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo Python found!
echo.

REM Check if pip is available
echo [2/6] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Installing pip...
    python -m ensurepip --upgrade
)
python -m pip --version
echo pip found!
echo.

REM Create virtual environment
echo [3/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    echo Virtual environment created!
)
echo.

REM Activate virtual environment and upgrade pip
echo [4/6] Activating virtual environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo.

REM Install Python dependencies
echo [5/6] Installing Python dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    echo Dependencies installed!
) else (
    echo WARNING: requirements.txt not found!
)
echo.

REM Create .env file from template
echo [6/6] Setting up environment file...
if exist .env (
    echo .env file already exists. Skipping...
) else (
    if exist env.template (
        copy env.template .env >nul
        echo .env file created from template!
        echo Please edit .env file with your configuration.
    ) else (
        echo WARNING: env.template not found!
    )
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Install Ollama from: https://ollama.ai/download
echo 3. Run: ollama pull llama3.2
echo 4. Activate virtual environment: venv\Scripts\activate
echo 5. Run application: python run.py
echo.
echo For detailed instructions, see docs/README.md
echo.
pause

