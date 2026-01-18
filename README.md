# User Story Automation

AI-powered application for generating user stories, epics, and test cases from project documents using Large Language Models (LLMs).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama (for local LLM) or API keys for OpenAI/Groq
- Google OAuth credentials (for authentication)

### Installation

#### Ubuntu/Linux (Recommended - One Script Installs Everything!)

```bash
# Clone the repository
git clone <repository-url>
cd user-story-automation

# Run complete automated setup (installs EVERYTHING)
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh

# The script automatically installs:
# ✅ Python 3.11+ and pip
# ✅ System dependencies
# ✅ Python virtual environment
# ✅ All Python packages
# ✅ Ollama (LLM runtime)
# ✅ Ollama model (llama3.2)
# ✅ Environment configuration

# After setup completes, just run:
source venv/bin/activate
python run.py
```

See [docs/UBUNTU_SETUP.md](docs/UBUNTU_SETUP.md) for detailed Ubuntu setup guide.

#### Windows

```bash
# Run automated setup
.\scripts\setup\setup.ps1
# Or
scripts\setup\setup.bat

# Activate virtual environment
venv\Scripts\activate

# Run the application
python run.py
```

#### Manual Setup

1. **Set up environment**
   ```bash
   # Copy environment template
   cp config/env.template .env
   
   # Edit .env with your configuration
   # See docs/UBUNTU_SETUP.md for detailed instructions
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

- **[Installation Guide](INSTALL.md)** - Complete installation instructions
- **[Ubuntu Setup](docs/UBUNTU_SETUP.md)** - Detailed Ubuntu/Linux setup
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Directory organization

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

- `scripts/setup/setup.sh` - Automated setup (Linux/Ubuntu)
- `scripts/setup/setup.bat` / `setup.ps1` - Automated setup (Windows)
- `pytest tests/` - Run tests (use pytest directly)
- `scripts/start.sh` / `stop.sh` - Server management (Linux/Ubuntu)

## 📄 License

ISC

## 🤝 Support

For issues or questions:
1. Check the documentation in `docs/` folder
2. Review troubleshooting sections
3. Check application logs in `data/logs/app.log`

## 📖 Additional Resources

- [Installation Guide](INSTALL.md) - Complete installation instructions
- [Ubuntu Setup Guide](docs/UBUNTU_SETUP.md) - Complete Ubuntu/Linux setup
- [Google Auth Setup](docs/GOOGLE_AUTH_SETUP.md) - OAuth configuration
- [SMTP Email Setup](docs/SMTP_EMAIL_SETUP.md) - Email configuration
