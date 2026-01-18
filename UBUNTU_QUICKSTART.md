# Ubuntu Quick Start Guide

Quick setup guide for running User Story Automation on Ubuntu Linux.

## Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install -y python3.11 python3.11-venv python3.11-pip python3-pip

# Install build tools (needed for some Python packages)
sudo apt install -y build-essential
```

## Quick Setup (One Script Does Everything!)

```bash
# 1. Navigate to project directory
cd /path/to/user-story-automation

# 2. Run complete automated setup (installs EVERYTHING)
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh

# The script will automatically install:
# ✅ Python 3.11+ and pip
# ✅ System dependencies
# ✅ Python virtual environment
# ✅ All Python packages
# ✅ Ollama (LLM runtime)
# ✅ Ollama model (llama3.2)
# ✅ Environment configuration

# 3. After setup completes, just run:
source venv/bin/activate
python run.py
```

That's it! The setup script handles everything. You just need to run it and then start the app.

## Access Application

Open browser: http://localhost:5000

## Environment Variables (.env)

Minimum required configuration:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
PORT=5000
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

## Troubleshooting

### Python Not Found
```bash
# Use python3 explicitly
python3 run.py

# Or create alias
alias python=python3
```

### Permission Denied
```bash
chmod +x scripts/setup/setup.sh
chmod +x scripts/*.sh
```

### Port Already in Use
```bash
# Find process using port 5000
sudo lsof -i :5000
# Kill it or change PORT in .env
```

### Ollama Not Running
```bash
# Start Ollama
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

## Full Documentation

See [docs/UBUNTU_SETUP.md](docs/UBUNTU_SETUP.md) for complete Ubuntu setup guide.
