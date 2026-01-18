# User Story Automation

AI-powered application for generating user stories, epics, and test cases from project documents using Large Language Models (LLMs).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama (for local LLM) or API keys for OpenAI/Groq
- Google OAuth credentials (for authentication)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd user-story-automation
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp config/env.template .env
   
   # Edit .env with your configuration
   # See docs/SETUP.md for detailed instructions
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
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

- **[Setup Guide](docs/SETUP.md)** - Complete setup instructions
- **[Architecture](docs/ARCHITECTURE_SEPARATION.md)** - Architecture overview
- **[Project Structure](PROJECT_STRUCTURE.md)** - Directory organization
- **[Requirements](docs/REQUIREMENTS.md)** - Requirements checklist

## 🏗️ Architecture

The application follows a clean separation of concerns:

- **Core Engine** (`src/core_engine/`) - Independent business logic
- **Backend** (`src/backend/`) - Flask API server
- **Frontend** (`src/frontend/`) - Web interface

Each component can be developed independently. See [docs/ARCHITECTURE_SEPARATION.md](docs/ARCHITECTURE_SEPARATION.md) for details.

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

- `scripts/setup/setup.bat` / `setup.ps1` - Automated setup (Windows)
- `scripts/validate_setup.py` - Validate installation
- `pytest tests/` - Run tests (use pytest directly)
- `scripts/start.sh` / `stop.sh` - Server management (Linux/Mac)

## 📄 License

ISC

## 🤝 Support

For issues or questions:
1. Check the documentation in `docs/` folder
2. Review troubleshooting sections
3. Check application logs in `data/logs/app.log`

## 📖 Additional Resources

- [Python Installation Guide](docs/PYTHON_INSTALLATION.md)
- [Ollama Setup Guide](docs/OLLAMA_SETUP.md)
- [Google Auth Setup](docs/GOOGLE_AUTH_SETUP.md)
- [SMTP Email Setup](docs/SMTP_EMAIL_SETUP.md)
