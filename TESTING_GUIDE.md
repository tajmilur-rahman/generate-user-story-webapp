# Testing the Ubuntu Setup on Windows

This guide walks you through testing the Ubuntu setup process using WSL on your Windows machine.

---

## Quick Start (5 minutes)

### Step 1: Run the Test Script

Open **PowerShell as Administrator** and run:

```powershell
cd C:\dev\User-story\user-story-automation
.\test-wsl-setup.ps1
```

This script will:
- ✅ Check if WSL is installed (install if needed)
- ✅ Check if Ubuntu is installed (install if needed)
- ✅ Verify WSL 2 is being used
- ✅ Check project directory accessibility
- ✅ Create a test environment script
- ✅ Launch Ubuntu terminal

### Step 2: Test Ubuntu Environment

Once in Ubuntu terminal:

```bash
cd /mnt/c/dev/User-story/user-story-automation
bash test-ubuntu-env.sh
```

This will verify:
- Ubuntu version
- Available memory
- Disk space
- Project directory access
- Setup guide availability

### Step 3: Follow the Setup Guide

```bash
# View the setup guide
cat UBUNTU_SETUP.md | less
# Press 'q' to exit, Space to scroll down

# Or view in sections
head -50 UBUNTU_SETUP.md  # First 50 lines
```

### Step 4: Start the Setup Process

Follow each step in `UBUNTU_SETUP.md`:

```bash
# Step 1: Update System
sudo apt update
sudo apt upgrade -y

# Step 2: Install Git
sudo apt install -y git

# Continue with remaining steps...
```

---

## Detailed Testing Instructions

### Phase 1: Environment Setup (10 minutes)

1. **Install WSL** (if not already installed):
   ```powershell
   # PowerShell as Administrator
   wsl --install
   # Restart computer
   ```

2. **Launch Ubuntu**:
   - Open "Ubuntu" from Start Menu
   - Create username and password on first launch

3. **Update Ubuntu**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### Phase 2: Test Each Setup Step (30-40 minutes)

Go through each step in `UBUNTU_SETUP.md` and document:

#### Checklist:

- [ ] **Step 1: Update System**
  - Command works without errors?
  - Time taken: _____ minutes
  - Issues encountered: _____

- [ ] **Step 2: Install Git**
  - Git installed successfully?
  - Version: _____
  - Issues: _____

- [ ] **Step 3: Clone Repository**
  - Can access Windows files from Ubuntu?
  - Clone successful?
  - Issues: _____

- [ ] **Step 4: Install Python 3.11+**
  - Python 3.11+ installed?
  - Version: _____
  - PPA added successfully?
  - Issues: _____

- [ ] **Step 5: Install Build Tools**
  - All tools installed?
  - Issues: _____

- [ ] **Step 6: Create Virtual Environment**
  - Venv created successfully?
  - Can activate venv?
  - Time taken: _____ seconds
  - Issues: _____

- [ ] **Step 7: Install Python Dependencies**
  - All packages installed?
  - Any package failures?
  - Time taken: _____ minutes
  - Issues: _____

- [ ] **Step 8: Install Ollama**
  - Ollama installed successfully?
  - Version: _____
  - Issues: _____

- [ ] **Step 9: Download LLM Model**
  - Model downloaded successfully?
  - Download size: _____
  - Time taken: _____ minutes
  - Issues: _____

- [ ] **Step 10: Setup Environment Variables**
  - .env file created?
  - Secret key generated?
  - All variables set correctly?
  - Issues: _____

- [ ] **Step 11: Setup Google OAuth** (Optional)
  - Skipped or completed?
  - Issues: _____

- [ ] **Step 12: Run the Application**
  - Application starts without errors?
  - Port 5000 accessible?
  - Issues: _____

- [ ] **Step 13: Access the Application**
  - Can access from Windows browser?
  - URL: http://localhost:5000
  - Interface loads correctly?
  - Issues: _____

### Phase 3: Functionality Testing (10 minutes)

- [ ] **Upload Document**
  - Can upload .docx file?
  - File accepted?
  - Issues: _____

- [ ] **Generate Stories**
  - Stories generated successfully?
  - Number of stories: _____
  - Quality acceptable?
  - Time taken: _____ seconds
  - Issues: _____

- [ ] **Export Results**
  - Can export as JSON?
  - Can export as Word?
  - Files downloaded correctly?
  - Issues: _____

---

## Common Issues & Solutions

### Issue: WSL not installing

**Solution:**
1. Enable Virtualization in BIOS
2. Run Windows Update
3. Try manual installation:
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

### Issue: Ubuntu terminal closes immediately

**Solution:**
1. Check if WSL 2 is installed:
   ```powershell
   wsl -l -v
   ```
2. Upgrade to WSL 2 if needed:
   ```powershell
   wsl --set-version Ubuntu 2
   ```

### Issue: Can't access Windows files

**Solution:**
Windows drives are mounted at `/mnt/`:
```bash
cd /mnt/c/dev/User-story/user-story-automation
```

### Issue: Permission denied errors

**Solution:**
Don't use `sudo` with pip inside venv:
```bash
# Wrong
sudo pip install -r requirements.txt

# Correct
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Ollama won't start

**Solution:**
```bash
# Check if already running
pgrep ollama

# Kill existing process
pkill ollama

# Start fresh
ollama serve &
```

### Issue: Port 5000 already in use

**Solution:**
```bash
# Find process using port 5000
sudo lsof -ti:5000

# Kill the process
sudo kill -9 $(sudo lsof -ti:5000)
```

---

## Testing Tips

### 1. Take Notes

Document everything:
- Commands that worked
- Commands that failed
- Error messages (exact text)
- Time taken for each step
- System specifications

### 2. Test Multiple Times

1. **First run**: Follow the guide exactly
2. **Second run**: Try to break it (skip steps, wrong commands)
3. **Third run**: Test on a fresh Ubuntu install

### 3. Reset Environment

To start fresh:
```powershell
# PowerShell as Administrator
wsl --unregister Ubuntu
wsl --install -d Ubuntu
```

### 4. Monitor Resources

```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check CPU usage
top
# Press 'q' to exit
```

### 5. Check Logs

```bash
# Application logs
tail -f data/logs/app.log

# System logs
dmesg | tail -20
```

---

## Performance Comparison

Test and document performance:

| Metric | Windows | WSL Ubuntu | Real Ubuntu |
|--------|---------|------------|-------------|
| Setup time | ___ min | ___ min | ___ min |
| Venv creation | ___ sec | ___ sec | ___ sec |
| Pip install | ___ min | ___ min | ___ min |
| Model download | ___ min | ___ min | ___ min |
| Story generation | ___ sec | ___ sec | ___ sec |

---

## Reporting Issues

If you find issues, document:

1. **Step number** where issue occurred
2. **Exact command** that was run
3. **Error message** (full text)
4. **Ubuntu version**: `lsb_release -a`
5. **Python version**: `python3 --version`
6. **System info**: `free -h && df -h`

---

## Success Criteria

The setup is successful if:

- ✅ All steps complete without errors
- ✅ Application starts and runs
- ✅ Can access from Windows browser
- ✅ Can upload documents
- ✅ Can generate user stories
- ✅ Can export results
- ✅ Total time < 45 minutes

---

## Next Steps After Testing

1. **Update UBUNTU_SETUP.md** with any improvements
2. **Add troubleshooting tips** for issues found
3. **Optimize time estimates** based on actual results
4. **Test on real Ubuntu** (if available)
5. **Get feedback** from others testing the setup

---

## Quick Commands Reference

```bash
# Navigate to project
cd /mnt/c/dev/User-story/user-story-automation

# View setup guide
cat UBUNTU_SETUP.md | less

# Check Ubuntu version
lsb_release -a

# Check system resources
free -h && df -h

# Activate venv
source venv/bin/activate

# Start Ollama
ollama serve &

# Run application
python run.py

# Check if app is running
curl http://localhost:5000/api/health

# Stop Ollama
pkill ollama

# Exit Ubuntu
exit
```

---

**Happy Testing! 🚀**

Document everything and update the guides based on your findings!
