# Complete Installation Guide

## One-Command Setup (Ubuntu/Linux)

After cloning the repository, run a single command to install everything:

```bash
chmod +x scripts/setup/setup.sh && ./scripts/setup/setup.sh
```

That's it! The script will install:
- ✅ Python 3.11+ and pip
- ✅ System build dependencies
- ✅ Python virtual environment
- ✅ All Python packages from requirements.txt
- ✅ Ollama (LLM runtime)
- ✅ Ollama model (llama3.2)
- ✅ Environment configuration (.env file with auto-generated secret key)

## After Setup

Once the setup script completes:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python run.py
```

Open your browser: **http://localhost:5000**

## What Gets Installed

### System Packages
- `build-essential` - Compiler tools for Python packages
- `python3.11` - Python 3.11 interpreter
- `python3.11-venv` - Virtual environment support
- `python3.11-dev` - Python development headers
- `python3-pip` - Python package manager
- `curl`, `wget`, `git` - Utility tools
- `sqlite3` - Database (for user management)
- `ca-certificates`, `gnupg` - Security certificates

### Python Packages (from requirements.txt)
- `flask` - Web framework
- `flask-cors` - CORS support
- `python-docx` - Word document processing
- `langchain-openai` - OpenAI integration
- `langchain-ollama` - Ollama integration
- `langchain-groq` - Groq integration
- `langchain-core` - LangChain core
- `python-dotenv` - Environment variable management
- `werkzeug` - WSGI utilities
- `Flask-Login` - User authentication
- `Authlib` - OAuth support
- `Flask-SQLAlchemy` - Database ORM
- `pytest` - Testing framework

### Ollama
- Ollama runtime (installed via official installer)
- llama3.2 model (downloaded automatically)

### Configuration
- `.env` file created from template
- Secret key auto-generated
- Default configuration set for Ollama

## Verification

After setup, verify everything is installed:

```bash
# Check Python
python --version  # Should show Python 3.11+

# Check virtual environment
source venv/bin/activate
which python  # Should point to venv/bin/python

# Check Ollama
ollama --version
ollama list  # Should show llama3.2

# Check Ollama is running
curl http://localhost:11434/api/tags
```

## Troubleshooting

### Setup Script Fails

If the script fails at any step:

1. **Check error message** - The script will show what failed
2. **Run failed step manually** - See detailed steps in docs/UBUNTU_SETUP.md
3. **Check logs** - Some operations may have detailed output

### Ollama Installation Issues

If Ollama fails to install:

```bash
# Try manual installation
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
which ollama
ollama --version
```

### Model Download Fails

If model download fails:

```bash
# Start Ollama manually
ollama serve

# In another terminal, download model
ollama pull llama3.2

# Verify
ollama list
```

### Permission Issues

If you get permission errors:

```bash
# Make scripts executable
chmod +x scripts/setup/setup.sh
chmod +x scripts/*.sh

# Fix file ownership
sudo chown -R $USER:$USER .
```

## Next Steps

1. ✅ Setup complete - All dependencies installed
2. ✅ Run application - `python run.py`
3. ⚙️ (Optional) Configure Google OAuth - Edit `.env` file
4. 📖 Read documentation - See `docs/` folder

## Platform Support

- ✅ **Ubuntu 20.04+** - Fully tested
- ✅ **Ubuntu 22.04+** - Fully tested
- ✅ **Debian** - Should work (not tested)
- ✅ **Other Linux distributions** - May need minor adjustments

## Manual Installation

If you prefer manual installation, see:
- [Ubuntu Setup Guide](docs/UBUNTU_SETUP.md) - Detailed manual steps
- [Cross-Platform Guide](docs/CROSS_PLATFORM_COMPATIBILITY.md) - Platform differences
