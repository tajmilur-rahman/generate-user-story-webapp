# User Story Automation - Complete Setup Guide

Full-stack application for generating and managing user stories from project documents using AI-powered LLM processing.

## 🚀 Quick Start

### Prerequisites Installation

1. **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - For Ubuntu/Linux: The setup script installs Python automatically

2. **Ollama (Recommended for Free Local LLM)** - [Download Ollama](https://ollama.ai/download)
   - **Windows**: Download installer from [Ollama Windows](https://ollama.ai/download/windows)
   - **macOS**: Download from [Ollama macOS](https://ollama.ai/download/macos) or use Homebrew: `brew install ollama`
   - **Linux**: Run `curl -fsSL https://ollama.ai/install.sh | sh` or use the automated setup script
   - For Ubuntu/Linux: The setup script installs Ollama and downloads the model automatically

3. **Google OAuth Credentials** (for user authentication)
   - See [Google Auth Setup Guide](GOOGLE_AUTH_SETUP.md)

4. **SMTP Configuration** (optional, for welcome emails)
   - See [SMTP Email Setup Guide](SMTP_EMAIL_SETUP.md)

### Automated Setup

Run the setup script to install everything automatically:

**Linux/Ubuntu (Manual Installation):**
```bash
# See UBUNTU_SETUP.md for complete step-by-step instructions
```

This script will automatically install:
- ✅ Python 3.11+ and pip
- ✅ System build dependencies
- ✅ Python virtual environment
- ✅ All Python packages
- ✅ Ollama (LLM runtime)
- ✅ Ollama model (llama3.2)
- ✅ Environment configuration (.env file)

After setup completes, just run:
```bash
source venv/bin/activate
python run.py
```

**Windows:**
```bash
# Install Python 3.11+ from python.org
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama from ollama.ai/download/windows
# Run application
python run.py
```

### Manual Setup

1. **Install Python Dependencies:**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Install packages
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables:**
   ```bash
   # Copy template
   copy config\env.template .env
   
   # Edit .env file with your configuration
   ```

3. **Start Ollama (if using local LLM):**
   ```bash
   ollama serve
   # In another terminal, pull a model:
   ollama pull llama3.2
   ```

4. **Run the Application:**
   ```bash
   python run.py
   ```

5. **Access the Application:**
   - Frontend & API: http://localhost:5000
   - Health check: http://localhost:5000/api/health

## 📦 Installation Requirements

### Required Software

| Software | Version | Download Link | Purpose |
|----------|---------|--------------|---------|
| **Python** | 3.11+ | [Download](https://www.python.org/downloads/) | Backend runtime |
| **Ollama** | Latest | [Download](https://ollama.ai/download) | Local LLM (recommended) |
| **Git** | Latest | [Download](https://git-scm.com/downloads) | Version control (optional) |

### Python Packages

All Python dependencies are listed in `requirements.txt`:
- Flask (web framework)
- LangChain (LLM integration)
- python-docx (document processing)
- Flask-Login, Authlib (authentication)
- And more...

Install with: `pip install -r requirements.txt`

### Ollama Models

Recommended models (choose one):
- **llama3.2** (recommended, balanced): `ollama pull llama3.2`
- **mistral** (fast, efficient): `ollama pull mistral`
- **qwen2.5** (multilingual): `ollama pull qwen2.5`

## 🔧 Configuration

### Environment Variables (.env file)

Create a `.env` file from `config/env.template`:

```bash
# LLM Provider (ollama, openai, or groq)
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Google OAuth (required for authentication)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# SMTP Email (optional, for welcome emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Flask Configuration
PORT=5000
SECRET_KEY=your-secret-key-here
```

See `config/env.template` for all available options.

## 📚 Documentation

- **[Ubuntu Setup Guide](../UBUNTU_SETUP.md)** - Complete Ubuntu/Linux installation (tested & working)
- **[Quick Setup Guide](../QUICK_SETUP.md)** - All commands in one place (fastest)
- **[Testing Setup Script](TESTING_SETUP_SCRIPT.md)** - How to test the Ubuntu setup script on Windows using WSL
- **[Google Auth Setup](GOOGLE_AUTH_SETUP.md)** - OAuth configuration guide
- **[SMTP Email Setup](SMTP_EMAIL_SETUP.md)** - Email configuration guide

## 🎯 Features

- **Document Upload**: Upload .docx, .doc, .txt, or .md files
- **AI-Powered Generation**: Uses LLM to generate user stories, epics, and test cases
- **User Authentication**: Google OAuth login
- **Welcome Emails**: Automatic email on first login (if SMTP configured)
- **Story Management**: View, integrate, and export user stories
- **Multiple LLM Support**: Ollama (local), OpenAI, or Groq

## 🏃 Running the Application

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the application
python run.py
```

The server starts on `http://localhost:5000`

## 🛠️ Project Structure

```
.
├── src/
│   ├── backend/          # Flask backend
│   │   ├── app.py        # Main application
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   └── models/       # Database models
│   └── frontend/         # Frontend assets
├── autoAgile1212/        # Integrated prompts and utilities
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── env.template          # Environment variables template
└── run.py               # Application launcher
```

## 🔍 Troubleshooting

### Setup Script Errors
- **MySQL/package errors**: See [Setup Errors Guide](troubleshooting/setup-errors.md)
- **Python 3.11 not found**: See [Setup Errors Guide](troubleshooting/setup-errors.md)
- **Permission denied**: See [Setup Errors Guide](troubleshooting/setup-errors.md)

### Python Issues
- For Ubuntu/Linux: Run the setup script which installs Python automatically
- For Windows: Download from [python.org](https://www.python.org/downloads/)

### Ollama Not Working
- Ensure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Pull model if missing: `ollama pull llama3.2`
- For Ubuntu/Linux: The setup script installs Ollama and downloads the model automatically

### Authentication Issues
- See [Google Auth Setup](GOOGLE_AUTH_SETUP.md)
- Verify OAuth credentials in `.env`

### Email Not Sending
- See [SMTP Email Setup](SMTP_EMAIL_SETUP.md)
- Check SMTP credentials in `.env`
- Verify email service logs

### Story Generation Issues
- Check the application logs in `data/logs/app.log` for detailed error messages
- Ensure your LLM provider (Ollama/OpenAI) is running and accessible
- Verify your document is in a supported format (.docx)

## 📝 API Endpoints

- `GET /api/health` - Health check
- `POST /api/generate-stories` - Generate stories from document
- `POST /api/integrate-story` - Integrate single story
- `POST /api/integrate-all` - Integrate all stories
- `GET /api/user` - Get current user info

## 🤝 Support

For issues or questions:
1. Check the documentation in `docs/` folder
2. Review troubleshooting sections
3. Check application logs in `data/logs/app.log`

## 📄 License

ISC
