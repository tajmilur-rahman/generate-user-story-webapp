# Python Installation Guide - Fresh Start

This guide will help you install Python and set up your User Story Automation project from scratch.

## Step 1: Install Python

### For Windows

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.11" or latest version (3.11+ recommended)
   - The installer will download automatically

2. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - **IMPORTANT:** Check the box "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open Command Prompt (cmd) or PowerShell
   - Run: `python --version`
   - You should see: `Python 3.11.x` or similar

### For macOS

1. **Using Homebrew (Recommended):**
   ```bash
   brew install python@3.11
   ```

2. **Or Download from Python.org:**
   - Go to: https://www.python.org/downloads/macos/
   - Download the installer for macOS
   - Run the installer and follow the prompts

3. **Verify Installation:**
   ```bash
   python3 --version
   ```

### For Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

Verify:
```bash
python3 --version
```

## Step 2: Verify Python Installation

Open a terminal/command prompt and run:

```bash
# Windows
python --version

# macOS/Linux
python3 --version
```

You should see Python 3.11 or higher.

## Step 3: Install pip (Python Package Manager)

pip usually comes with Python, but verify it's installed:

```bash
# Windows
python -m pip --version

# macOS/Linux
python3 -m pip --version
```

If pip is not found, install it:
```bash
# Windows
python -m ensurepip --upgrade

# macOS/Linux
python3 -m ensurepip --upgrade
```

## Step 4: Navigate to Project Directory

```bash
cd "C:\Users\avish\OneDrive\Desktop\User-story\user-story-automation"
```

## Step 5: Create Virtual Environment

A virtual environment isolates your project dependencies from other Python projects.

### Windows:
```bash
python -m venv venv
```

### macOS/Linux:
```bash
python3 -m venv venv
```

This creates a `venv` folder in your project directory.

## Step 6: Activate Virtual Environment

### Windows (Command Prompt):
```bash
venv\Scripts\activate
```

### Windows (PowerShell):
```bash
venv\Scripts\Activate.ps1
```

If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### macOS/Linux:
```bash
source venv/bin/activate
```

**You'll know it's activated when you see `(venv)` at the start of your command prompt.**

## Step 7: Upgrade pip (Recommended)

```bash
# Windows
python -m pip install --upgrade pip

# macOS/Linux
python3 -m pip install --upgrade pip
```

## Step 8: Install Project Dependencies

With the virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- LangChain (LLM integration)
- python-docx (document processing)
- And all other dependencies

## Step 9: Verify Installation

Check that packages are installed:

```bash
pip list
```

You should see all packages from `requirements.txt` listed.

## Step 10: Set Up Environment Variables

1. **Copy the template:**
   ```bash
   # Windows
   copy env.template .env

   # macOS/Linux
   cp env.template .env
   ```

2. **Edit `.env` file** with your configuration:
   - LLM provider settings
   - Google OAuth credentials
   - SMTP email settings (optional)
   - See `docs/SMTP_EMAIL_SETUP.md` for email configuration

## Step 11: Test the Installation

Run the application:

```bash
# Windows
python run.py

# macOS/Linux
python3 run.py
```

Or if using the Flask app directly:

```bash
# Windows
python src/backend/app.py

# macOS/Linux
python3 src/backend/app.py
```

The server should start on `http://localhost:5000`

## Troubleshooting

### "Python is not recognized" (Windows)

**Problem:** Python is not in your PATH

**Solution:**
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Python311` and `C:\Python311\Scripts` (adjust version number)

### "pip is not recognized"

**Solution:**
```bash
python -m pip install --upgrade pip
```

### Virtual Environment Issues

**If `venv` command doesn't work:**
```bash
# Install venv module
python -m pip install virtualenv

# Then create venv
python -m virtualenv venv
```

### Permission Errors (macOS/Linux)

**Solution:**
```bash
sudo python3 -m pip install --upgrade pip
```

Or use `--user` flag:
```bash
python3 -m pip install --user -r requirements.txt
```

### Port Already in Use

**Problem:** Port 5000 is already in use

**Solution:**
1. Change port in `.env`: `PORT=5001`
2. Or stop the other application using port 5000

## Quick Reference Commands

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py

# Deactivate virtual environment
deactivate
```

## Next Steps

After Python is installed and dependencies are set up:

1. **Configure LLM Provider:**
   - See `docs/SETUP.md` for LLM configuration
   - Choose: Ollama (local), OpenAI, or Groq

2. **Set Up Google OAuth:**
   - See `docs/GOOGLE_AUTH_SETUP.md`
   - Required for user authentication

3. **Configure SMTP (Optional):**
   - See `docs/GMAIL_SMTP_SETUP.md`
   - For welcome emails on first login

4. **Start Development:**
   - Run `python run.py`
   - Open `http://localhost:5000` in your browser

## Python Version Requirements

- **Minimum:** Python 3.9
- **Recommended:** Python 3.11 or 3.12
- **Not Supported:** Python 2.x (deprecated)

Check your version:
```bash
python --version
```

## Additional Resources

- Python Official Docs: https://docs.python.org/3/
- pip Documentation: https://pip.pypa.io/
- Virtual Environments: https://docs.python.org/3/tutorial/venv.html

