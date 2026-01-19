# User Story Automation

AI-powered application for generating user stories, epics, and test cases from project documents using Large Language Models (LLMs).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama (for local LLM) or API keys for OpenAI/Groq
- Google OAuth credentials (for authentication)

### Installation

#### Ubuntu/Linux (Tested & Working ✅)

**Quick Setup:** See **[QUICK_SETUP.md](QUICK_SETUP.md)** - All commands in one place (30-40 min)

**Detailed Guide:** See **[UBUNTU_SETUP.md](UBUNTU_SETUP.md)** - Step-by-step with explanations

Quick summary - all commands in one place:
```bash
# System setup
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common git zstd

# Python 3.11
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip build-essential curl sqlite3

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Python packages
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Ollama (manual installation - avoids snap issues)
cd /tmp
wget https://github.com/ollama/ollama/releases/download/v0.1.29/ollama-linux-amd64 -O ollama
chmod +x ollama
sudo mv ollama /usr/local/bin/ollama

# Start Ollama (Terminal 1 - keep running)
/usr/local/bin/ollama serve

# In new terminal: Download model
ollama pull llama3.2

# Setup environment
cp config/env.template .env
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
sed -i "s|^LLM_PROVIDER=.*|LLM_PROVIDER=ollama|" .env

# Run application
python run.py
```

**Time:** 30-40 minutes | **Browser:** http://localhost:5000

#### Windows

**Manual Installation:**
```bash
# 1. Install Python 3.11+ from python.org
# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Ollama from ollama.ai/download/windows
# 6. Run application
python run.py
```

See [UBUNTU_SETUP.md](UBUNTU_SETUP.md) for detailed instructions.

# Run the application
python run.py
```

#### Manual Setup

1. **Set up environment**
   ```bash
   # Copy environment template
   cp config/env.template .env
   
   # Edit .env with your configuration
   # See UBUNTU_SETUP.md for detailed instructions
   ```

2. **Install dependencies**
   ```bash
   # Create virtual environment
   python3 -m venv venv  # Linux/Ubuntu
   python -m venv venv    # Windows
   
   # Activate virtual environment
   source venv/bin/activate  # Linux/Ubuntu
   venv\Scripts\activate      # Windows
   
   # Install packages
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   - Frontend: http://localhost:5000
   - API: http://localhost:5000/api

## 📁 Project Structure

```
user-story-automation/
├── src/              # Source code
│   ├── backend/     # Flask backend
│   ├── core_engine/ # Core business logic
│   └── frontend/    # Web interface
├── tests/           # Test files
├── scripts/         # Utility scripts
├── config/          # Configuration files
├── data/            # Data files (logs, outputs)
└── docs/            # Documentation
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure documentation.

## 📚 Documentation

**Setup Guides:**
- **[Quick Setup](QUICK_SETUP.md)** ⚡ - All commands in one place (fastest)
- **[Ubuntu Setup](UBUNTU_SETUP.md)** 📖 - Detailed step-by-step guide (tested & working)
- **[Testing Guide](TESTING_GUIDE.md)** ✅ - Testing checklist and WSL instructions

**Reference:**
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Directory organization
- **[Cross-Platform](docs/CROSS_PLATFORM_COMPATIBILITY.md)** - Platform compatibility

## 🏗️ Architecture

The application follows a clean separation of concerns:

- **Core Engine** (`src/core_engine/`) - Independent business logic
- **Backend** (`src/backend/`) - Flask API server
- **Frontend** (`src/frontend/`) - Web interface

Each component can be developed independently. See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for architecture details.

## 🎯 Features

- **Document Upload** - Upload .docx, .doc, .txt, or .md files
- **AI-Powered Generation** - Uses LLM to generate user stories, epics, and test cases
- **User Authentication** - Google OAuth login
- **Story Management** - View, integrate, and export user stories
- **Multiple LLM Support** - Ollama (local), OpenAI, or Groq

## 🔧 Configuration

Create a `.env` file from `config/env.template`:

```bash
# LLM Provider (ollama, openai, or groq)
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Google OAuth (required)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Flask Configuration
PORT=5000
SECRET_KEY=your-secret-key-here
```

See `config/env.template` for all available options.

## 🧪 Testing

Run tests:
```bash
# Run all tests
pytest tests/

# Run specific test
python scripts/run_test.py
```

## 📝 Development

### Project Structure Principles

1. **Separation of Concerns** - Core engine is independent
2. **Clear Organization** - Related files grouped together
3. **No Root Clutter** - Minimal files at root level
4. **Logical Grouping** - Scripts, tests, docs organized by purpose

### Key Directories

- `src/core_engine/` - Core business logic (can be developed independently)
- `src/backend/` - Flask API (depends on core_engine)
- `src/frontend/` - Web UI (depends on backend API)
- `tests/` - All test files
- `scripts/` - Utility scripts
- `data/` - All data files (logs, outputs, uploads)
- `docs/` - All documentation

## 🛠️ Scripts

- See [QUICK_SETUP.md](QUICK_SETUP.md) or [UBUNTU_SETUP.md](UBUNTU_SETUP.md) for installation
- `pytest tests/` - Run tests (use pytest directly)

## 📄 License

ISC

## 🤝 Support

For issues or questions:
1. Check the documentation in `docs/` folder
2. Review troubleshooting sections
3. Check application logs in `data/logs/app.log`

## 📖 Additional Resources

- [Quick Setup Guide](QUICK_SETUP.md) - Fast Ubuntu installation (30-40 min)
- [Complete Ubuntu Setup](UBUNTU_SETUP.md) - Detailed Ubuntu installation guide
- [Google Auth Setup](docs/GOOGLE_AUTH_SETUP.md) - OAuth configuration
- [SMTP Email Setup](docs/SMTP_EMAIL_SETUP.md) - Email configuration
