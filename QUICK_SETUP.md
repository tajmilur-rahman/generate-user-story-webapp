# Quick Setup - All Commands in One Place

**Tested and working on Ubuntu 20.04+**

Copy and paste these command blocks in order. Total time: **30-40 minutes**.

---

## Block 1: System Setup (3-7 minutes)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common git zstd
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip build-essential curl sqlite3
```

---

## Block 2: Clone Repository (30 seconds)

```bash
cd ~
git clone <YOUR_REPOSITORY_URL>
cd user-story-automation
```

**Replace `<YOUR_REPOSITORY_URL>`** with your actual repository URL.

---

## Block 3: Python Setup (3-6 minutes)

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## Block 4: Install Ollama (3-5 minutes)

```bash
sudo snap remove ollama 2>/dev/null || true
cd /tmp
wget https://github.com/ollama/ollama/releases/download/v0.1.29/ollama-linux-amd64 -O ollama
chmod +x ollama
sudo mv ollama /usr/local/bin/ollama
/usr/local/bin/ollama --version
```

---

## Block 5: Setup Environment (1 minute)

```bash
cd ~/user-story-automation
cp config/env.template .env
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
sed -i "s|^LLM_PROVIDER=.*|LLM_PROVIDER=ollama|" .env
sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=llama3.2|" .env
sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://localhost:11434|" .env
```

---

## Block 6: Start Ollama (keep this terminal running)

```bash
/usr/local/bin/ollama serve
```

**Open a new terminal for the next steps.**

---

## Block 7: Download Model (5-15 minutes - in new terminal)

```bash
cd ~/user-story-automation
ollama pull llama3.2
ollama list
```

---

## Block 8: Run Application (in same terminal as Block 7)

```bash
source venv/bin/activate
python run.py
```

---

## Block 9: Access Application

Open browser: **http://localhost:5000**

---

## To Run Again Later

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

---

## One-Command Verification

```bash
python3.11 --version && ollama --version && which python | grep venv && echo "✅ All ready!"
```

---

**Total Time: 30-40 minutes** | **Tested on Ubuntu 22.04/24.04 via WSL**
