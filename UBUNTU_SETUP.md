# Complete Ubuntu Setup Guide - Tested & Working

This guide provides **tested, working commands** for setting up the User Story Automation application on Ubuntu from scratch.

**Total Time:** 30-40 minutes (depending on internet speed)

---

## Prerequisites

- Ubuntu 20.04 or newer
- Internet connection
- Terminal access
- At least 10 GB free disk space

---

## Complete Setup - Copy & Paste Commands

### **Step 1: Update System (2-5 minutes)**

```bash
sudo apt update
sudo apt upgrade -y
```

---

### **Step 2: Install Git (30 seconds)**

```bash
sudo apt install -y git
git --version
```

---

### **Step 3: Clone Repository (30 seconds)**

```bash
cd ~
git clone <YOUR_REPOSITORY_URL>
cd user-story-automation
```

**Replace `<YOUR_REPOSITORY_URL>`** with your actual repository URL.

---

### **Step 4: Install Python 3.11+ (2-5 minutes)**

```bash
# Install prerequisites
sudo apt install -y software-properties-common

# Add Python repository
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verify installation
python3.11 --version
```

**Expected output:** `Python 3.11.x`

---

### **Step 5: Install System Dependencies (1-2 minutes)**

```bash
sudo apt install -y build-essential curl sqlite3 zstd

# Verify
gcc --version
curl --version
```

---

### **Step 6: Create Virtual Environment (30-60 seconds)**

```bash
# Navigate to project directory
cd ~/user-story-automation

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**You should see `(venv)` at the start of your prompt.**

**Verify:**
```bash
which python
# Should show: /home/YOUR_USERNAME/user-story-automation/venv/bin/python
```

---

### **Step 7: Install Python Dependencies (2-5 minutes)**

```bash
# Make sure venv is activated (you should see (venv) in prompt)
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**This installs:** Flask, LangChain, python-docx, and all other dependencies.

---

### **Step 8: Install Ollama (2-5 minutes)**

```bash
# Remove any snap-based Ollama (if exists)
sudo snap remove ollama 2>/dev/null || true

# Install zstd (required for Ollama)
sudo apt install -y zstd

# Download Ollama binary
cd /tmp
wget https://github.com/ollama/ollama/releases/download/v0.1.29/ollama-linux-amd64 -O ollama

# Verify it's a binary (not HTML)
file ollama
# Should show: "ELF 64-bit LSB executable"

# Make executable and install
chmod +x ollama
sudo mv ollama /usr/local/bin/ollama

# Verify installation
/usr/local/bin/ollama --version
```

---

### **Step 9: Start Ollama and Download Model (5-15 minutes)**

**Terminal 1 (keep this running):**
```bash
# Start Ollama server
/usr/local/bin/ollama serve
```

**Terminal 2 (open a new Ubuntu terminal):**
```bash
# Wait a few seconds for Ollama to start, then:

# Test connection
curl http://localhost:11434/api/version

# Download model (this takes 5-15 minutes - it's a 2GB download)
ollama pull llama3.2

# Verify model is downloaded
ollama list
```

**Expected output:**
```
NAME            ID              SIZE    MODIFIED
llama3.2:latest a80c4f17acd5    2.0 GB  Less than a second ago
```

---

### **Step 10: Setup Environment Variables (1 minute)**

**In Terminal 2 (or a new terminal):**

```bash
cd ~/user-story-automation

# Copy template
cp config/env.template .env

# Generate secret key and configure
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
sed -i "s|^LLM_PROVIDER=.*|LLM_PROVIDER=ollama|" .env
sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=llama3.2|" .env
sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://localhost:11434|" .env

# Verify configuration
cat .env | grep -E "SECRET_KEY|LLM_PROVIDER|OLLAMA"
```

---

### **Step 11: Run the Application (10 seconds)**

**In Terminal 2:**

```bash
cd ~/user-story-automation

# Activate virtual environment
source venv/bin/activate

# Run the application
python run.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

---

### **Step 12: Access the Application**

Open your web browser and go to:
```
http://localhost:5000
```

**You should see the User Story Automation interface!** 🎉

---

## Quick Reference - After Initial Setup

### **To Run the Application:**

**Terminal 1:**
```bash
/usr/local/bin/ollama serve
```

**Terminal 2:**
```bash
cd ~/user-story-automation
source venv/bin/activate
python run.py
```

**Browser:**
```
http://localhost:5000
```

### **To Stop the Application:**
- Press `Ctrl + C` in Terminal 2 (Flask app)
- Press `Ctrl + C` in Terminal 1 (Ollama server)

---

## Optional: Setup Ollama as a System Service

For production or to auto-start Ollama on boot:

```bash
# Create ollama user
sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Create systemd service
sudo tee /etc/systemd/system/ollama.service > /dev/null <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=default.target
EOF

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Check status
sudo systemctl status ollama
```

**Now Ollama runs automatically!** Just run `python run.py` to start the Flask app.

---

## Troubleshooting

### Issue: `python3.11: command not found`
**Solution:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv
```

### Issue: `externally-managed-environment` error
**Solution:** Make sure virtual environment is activated:
```bash
source venv/bin/activate
# You should see (venv) in your prompt
```

### Issue: Ollama not starting
**Solution:**
```bash
# Check if already running
pgrep ollama

# Kill existing processes
pkill ollama

# Start again
/usr/local/bin/ollama serve
```

### Issue: Port 5000 already in use
**Solution:**
```bash
sudo lsof -ti:5000 | xargs kill -9
```

### Issue: Model download fails
**Solution:**
- Check internet connection
- Ensure Ollama server is running
- Try download again: `ollama pull llama3.2`

---

## System Requirements

**Minimum:**
- 4 GB RAM
- 10 GB free disk space (for model + dependencies)
- 2 CPU cores

**Recommended:**
- 8 GB RAM
- 20 GB free disk space
- 4 CPU cores

---

## Verification Checklist

- [ ] Ubuntu updated
- [ ] Git installed
- [ ] Python 3.11+ installed
- [ ] Build tools installed
- [ ] Virtual environment created
- [ ] Python dependencies installed
- [ ] Ollama installed
- [ ] Model downloaded (llama3.2)
- [ ] .env file configured
- [ ] Application runs without errors
- [ ] Can access at http://localhost:5000
- [ ] Can upload documents
- [ ] Can generate user stories

---

## Next Steps

1. **Upload a document** (.docx format) with your requirements
2. **Generate user stories** using the web interface
3. **Export results** as JSON or Word document
4. **Integrate with Jira** (if needed)

---

## Additional Configuration

### Google OAuth (Optional)
See [docs/GOOGLE_AUTH_SETUP.md](docs/GOOGLE_AUTH_SETUP.md) for adding user authentication.

### Email Notifications (Optional)
See [docs/SMTP_EMAIL_SETUP.md](docs/SMTP_EMAIL_SETUP.md) for email configuration.

---

## Need Help?

- Check logs: `data/logs/app.log`
- View documentation: `docs/README.md`
- Check troubleshooting section above

---

**Setup Complete! 🎉**

**Estimated Total Time:** 30-40 minutes
