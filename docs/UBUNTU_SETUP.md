# Ubuntu Setup Guide

Complete guide for setting up User Story Automation on Ubuntu Linux.

## Prerequisites

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python 3.11+

```bash
# Check Python version
python3 --version

# If Python 3.11+ is not installed:
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### 3. Install System Dependencies

```bash
# Install build essentials (needed for some Python packages)
sudo apt install -y build-essential

# Install other useful tools
sudo apt install -y git curl wget
```

## Installation Steps

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/user-story-automation
```

### Step 2: Run Automated Setup Script

```bash
# Make setup script executable
chmod +x scripts/setup/setup.sh

# Run setup script
./scripts/setup/setup.sh
```

The setup script will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all Python dependencies
- ✅ Create .env file from template

### Step 3: Run the Application

After the setup script completes successfully:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python run.py
```

The application will start on `http://localhost:5000`

**Note:** The setup script has already:
- ✅ Installed Ollama
- ✅ Started Ollama service
- ✅ Downloaded llama3.2 model
- ✅ Created .env file with default Ollama configuration
- ✅ Generated secret key automatically

### Optional: Configure Google OAuth

If you want to enable user authentication, edit `.env`:

```bash
nano .env
```

Add your Google OAuth credentials (see [Google Auth Setup](GOOGLE_AUTH_SETUP.md)):

```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

### Optional: Make Ollama Start Automatically

The setup script starts Ollama, but it won't persist after reboot. To make it start automatically:

```bash
# Create systemd service (optional)
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable ollama
sudo systemctl start ollama
```

## Running as a Service (Optional)

### Create Systemd Service

Create a service file:

```bash
sudo nano /etc/systemd/system/user-story-automation.service
```

Add the following (adjust paths as needed):

```ini
[Unit]
Description=User Story Automation Flask App
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/user-story-automation
Environment="PATH=/path/to/user-story-automation/venv/bin"
ExecStart=/path/to/user-story-automation/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable user-story-automation
sudo systemctl start user-story-automation

# Check status
sudo systemctl status user-story-automation

# View logs
sudo journalctl -u user-story-automation -f
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Find what's using the port
sudo lsof -i :5000
# or
sudo netstat -tlnp | grep :5000

# Kill the process or change PORT in .env
```

### Permission Errors

If you get permission errors:

```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/setup/*.sh

# Fix file permissions
sudo chown -R $USER:$USER .
```

### Python Not Found

If `python` command doesn't work:

```bash
# Use python3 explicitly
python3 run.py

# Or create alias
alias python=python3
```

### Virtual Environment Issues

If virtual environment has issues:

```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ollama Connection Issues

If Ollama can't connect:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Check firewall
sudo ufw status
sudo ufw allow 11434/tcp  # If using firewall
```

## File Paths

All file paths in the application use `os.path.join()` for cross-platform compatibility. Uploads are stored in the system temp directory (usually `/tmp` on Linux).

## Next Steps

1. ✅ Application is running
2. ✅ Open browser to `http://localhost:5000`
3. ✅ Upload a document and generate user stories
4. ✅ See [README.md](README.md) for usage instructions

## Additional Resources

- [Main README](README.md)
- [Ollama Setup](OLLAMA_SETUP.md)
- [Google Auth Setup](GOOGLE_AUTH_SETUP.md)
- [Project Structure](PROJECT_STRUCTURE.md)
