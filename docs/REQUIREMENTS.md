# Project Requirements Checklist

Use this checklist to ensure you have everything needed to run the User Story Automation project.

## ✅ Required Software

### 1. Python 3.11+
- [ ] **Download**: [Python Official Website](https://www.python.org/downloads/)
- [ ] **Version**: 3.11 or higher (3.12 recommended)
- [ ] **Installation**: Check "Add Python to PATH" during installation
- [ ] **Verify**: Run `python --version` in terminal
- [ ] **Documentation**: See [Python Installation Guide](docs/PYTHON_INSTALLATION.md)

### 2. Ollama (Recommended for Local LLM)
- [ ] **Download**: [Ollama Official Website](https://ollama.ai/download)
  - **Windows**: [Windows Installer](https://ollama.ai/download/windows)
  - **macOS**: [macOS Installer](https://ollama.ai/download/macos) or `brew install ollama`
  - **Linux**: Run `curl -fsSL https://ollama.ai/install.sh | sh`
- [ ] **Verify**: Run `ollama --version`
- [ ] **Start Service**: Run `ollama serve` (keep running)
- [ ] **Download Model**: Run `ollama pull llama3.2` (or `mistral`, `qwen2.5`)

### 3. Git (Optional, for version control)
- [ ] **Download**: [Git Official Website](https://git-scm.com/downloads)
- [ ] **Verify**: Run `git --version`

## ✅ Python Packages

All packages are listed in `requirements.txt`. Install with:
```bash
pip install -r requirements.txt
```

### Key Dependencies:
- [ ] Flask (web framework)
- [ ] LangChain (LLM integration)
- [ ] python-docx (document processing)
- [ ] Flask-Login, Authlib (authentication)
- [ ] Flask-SQLAlchemy (database)
- [ ] python-dotenv (environment variables)

## ✅ Configuration Files

### 1. Environment Variables (.env)
- [ ] **Create**: Copy `env.template` to `.env`
- [ ] **Configure LLM Provider**: Set `LLM_PROVIDER=ollama` (or `openai`, `groq`)
- [ ] **Configure Ollama**: Set `OLLAMA_BASE_URL` and `OLLAMA_MODEL`
- [ ] **Configure Google OAuth**: Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- [ ] **Configure SMTP** (optional): Set SMTP settings for welcome emails
- [ ] **Set Secret Key**: Generate and set `SECRET_KEY`

### 2. Google OAuth Credentials
- [ ] **Create Project**: [Google Cloud Console](https://console.cloud.google.com/)
- [ ] **Enable OAuth**: Enable Google+ API
- [ ] **Create Credentials**: Create OAuth 2.0 Client ID
- [ ] **Add to .env**: Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- [ ] **Documentation**: See [Google Auth Setup Guide](docs/GOOGLE_AUTH_SETUP.md)

### 3. SMTP Email (Optional)
- [ ] **Enable 2FA**: Enable 2-Factor Authentication in Google Account
- [ ] **Generate App Password**: [Google App Passwords](https://myaccount.google.com/apppasswords)
- [ ] **Add to .env**: Add SMTP configuration
- [ ] **Documentation**: See [SMTP Email Setup Guide](docs/SMTP_EMAIL_SETUP.md)

## ✅ Setup Steps

### Automated Setup (Windows)
- [ ] Run `setup.bat` or `setup.ps1` to install dependencies automatically

### Manual Setup
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment:
  - Windows: `venv\Scripts\activate`
  - macOS/Linux: `source venv/bin/activate`
- [ ] Upgrade pip: `pip install --upgrade pip`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create .env file: `copy env.template .env` (Windows) or `cp env.template .env` (macOS/Linux)

## ✅ Verification

### Test Python Installation
```bash
python --version  # Should show Python 3.11+
pip --version     # Should show pip version
```

### Test Ollama Installation
```bash
ollama --version           # Should show Ollama version
ollama list                # Should show downloaded models
ollama pull llama3.2      # Download model if not present
```

### Test Application
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run application
python run.py

# Should see:
# [STARTING] User Story Automation Server
# Frontend: http://localhost:5000
```

## 📋 Quick Installation Commands

### Windows (PowerShell)
```powershell
# Install Python dependencies
.\setup.ps1

# Or manually:
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS/Linux
```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Install Ollama
```bash
# Windows: Download from https://ollama.ai/download/windows
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# After installation:
ollama serve          # Start Ollama service
ollama pull llama3.2 # Download model
```

## 🔗 Important Links

- **Python**: https://www.python.org/downloads/
- **Ollama**: https://ollama.ai/download
- **Google Cloud Console**: https://console.cloud.google.com/
- **Google App Passwords**: https://myaccount.google.com/apppasswords

## 📚 Documentation

- [README.md](docs/README.md) - Main setup guide
- [Python Installation Guide](docs/PYTHON_INSTALLATION.md) - Detailed Python setup
- [Google Auth Setup](docs/GOOGLE_AUTH_SETUP.md) - OAuth configuration
- [SMTP Email Setup](docs/SMTP_EMAIL_SETUP.md) - Email configuration

## ⚠️ Common Issues

### Python not found
- Make sure Python is added to PATH
- Reinstall Python and check "Add Python to PATH"

### Ollama not working
- Ensure Ollama service is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Pull model if missing: `ollama pull llama3.2`

### Dependencies not installing
- Upgrade pip: `pip install --upgrade pip`
- Use virtual environment
- Check Python version: `python --version`

### Port 5000 already in use
- Change port in `.env`: `PORT=5001`
- Or stop the application using port 5000

## ✅ Ready to Run?

Once all items are checked:
1. Activate virtual environment
2. Start Ollama: `ollama serve`
3. Run application: `python run.py`
4. Open browser: http://localhost:5000

