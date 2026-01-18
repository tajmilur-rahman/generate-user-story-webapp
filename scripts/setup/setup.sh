#!/bin/bash

# ============================================================================
# User Story Automation - Complete Setup Script for Ubuntu/Linux
# This script installs EVERYTHING needed to run the application
# ============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored messages
print_step() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running as root (we don't want that for most operations)
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run this script as root/sudo"
    print_info "The script will ask for sudo password when needed"
    exit 1
fi

print_step "User Story Automation - Complete Setup"
echo "This script will install:"
echo "  • Python 3.11+ and pip"
echo "  • System build dependencies"
echo "  • Python virtual environment"
echo "  • All Python packages"
echo "  • Ollama (LLM runtime)"
echo "  • Ollama model (llama3.2)"
echo "  • Environment configuration"
echo ""
echo "Note: If Python 3.11 is not in default repositories,"
echo "      the script will add the deadsnakes PPA automatically."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# ============================================================================
# STEP 1: Fix Broken Packages and Update System
# ============================================================================
print_step "[1/10] Fixing broken packages and updating system..."

# Fix any broken package installations first
print_info "Checking for broken packages..."
if dpkg -l | grep -q "^..r"; then
    print_info "Found broken packages. Attempting to fix..."
    sudo dpkg --configure -a || true
    sudo apt --fix-broken install -y || true
fi

# Update package lists
print_info "Updating package lists..."
sudo apt update

# Install software-properties-common early (needed for add-apt-repository)
if ! dpkg -l | grep -q software-properties-common; then
    print_info "Installing software-properties-common..."
    sudo apt install -y software-properties-common
fi

# Check if MySQL is in a broken state and fix it
if dpkg -l | grep -q "^..r.*mysql"; then
    print_info "Detected broken MySQL packages. Attempting to fix..."
    sudo dpkg --configure -a || true
    sudo apt --fix-broken install -y || true
    
    # If still broken, offer to remove (but don't force it)
    if dpkg -l | grep -q "^..r.*mysql"; then
        print_error "MySQL packages are still broken after fix attempt"
        print_info "You may need to manually fix MySQL:"
        print_info "  sudo dpkg --configure -a"
        print_info "  sudo apt --fix-broken install"
        print_info "Or remove MySQL if not needed:"
        print_info "  sudo apt remove --purge mysql-server mysql-common"
        print_info "Continuing with setup (MySQL is not required for this project)..."
    fi
fi

print_success "System packages updated"

# ============================================================================
# STEP 2: Check and Setup Python 3.11
# ============================================================================
print_step "[2/10] Checking Python installation..."

# Check if python3.11 is already available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION=$(python3.11 --version)
    print_success "Python 3.11 found: $PYTHON_VERSION"
    PYTHON_NEEDS_INSTALL=false
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version)
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        print_info "Python 3.11+ is required. Found: $PYTHON_VERSION"
        print_info "Adding deadsnakes PPA for Python 3.11..."
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        PYTHON_NEEDS_INSTALL=true
    else
        print_success "Python found: $PYTHON_VERSION (meets requirements)"
        PYTHON_NEEDS_INSTALL=false
        # Use existing python3 if it's 3.11+
        PYTHON_CMD="python3"
    fi
else
    print_info "Python not found. Adding deadsnakes PPA for Python 3.11..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    PYTHON_NEEDS_INSTALL=true
fi

# Install Python 3.11 if needed
if [ "$PYTHON_NEEDS_INSTALL" = true ]; then
    print_info "Installing Python 3.11..."
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
    PYTHON_CMD="python3.11"
    print_success "Python 3.11 installed"
fi

# ============================================================================
# STEP 3: Install System Dependencies
# ============================================================================
print_step "[3/10] Installing system dependencies..."

# Try to install dependencies, with error handling
if ! sudo apt install -y \
    build-essential \
    python3-pip \
    curl \
    wget \
    git \
    sqlite3 \
    ca-certificates \
    gnupg \
    lsb-release; then
    
    print_error "Failed to install some dependencies. Attempting to fix..."
    
    # Fix broken packages
    sudo dpkg --configure -a || true
    sudo apt --fix-broken install -y || true
    
    # Try again
    sudo apt install -y \
        build-essential \
        python3-pip \
        curl \
        wget \
        git \
        sqlite3 \
        ca-certificates \
        gnupg \
        lsb-release || {
        print_error "Failed to install dependencies after fix attempt"
        print_info "You may need to manually fix broken packages:"
        print_info "  sudo dpkg --configure -a"
        print_info "  sudo apt --fix-broken install"
        exit 1
    }
fi

print_success "System dependencies installed"

# ============================================================================
# STEP 4: Verify Python Installation
# ============================================================================
print_step "[4/10] Verifying Python installation..."
if command -v $PYTHON_CMD &> /dev/null; then
    FINAL_VERSION=$($PYTHON_CMD --version)
    print_success "Python ready: $FINAL_VERSION"
else
    print_error "Python installation verification failed"
    exit 1
fi

# ============================================================================
# STEP 5: Check/Install pip
# ============================================================================
print_step "[5/10] Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_info "Installing pip..."
    sudo apt install -y python3-pip
fi

# Upgrade pip
$PYTHON_CMD -m pip install --upgrade pip --quiet
print_success "pip is ready"

# ============================================================================
# STEP 6: Create Virtual Environment
# ============================================================================
print_step "[6/10] Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Upgrade pip in venv
python -m pip install --upgrade pip --quiet
print_success "pip upgraded in virtual environment"

# ============================================================================
# STEP 7: Install Python Dependencies
# ============================================================================
print_step "[7/10] Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    print_info "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# ============================================================================
# STEP 8: Install Ollama
# ============================================================================
print_step "[8/10] Installing Ollama..."

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "installed")
    print_success "Ollama already installed: $OLLAMA_VERSION"
else
    print_info "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Verify installation
    if command -v ollama &> /dev/null; then
        print_success "Ollama installed successfully"
    else
        print_error "Ollama installation failed"
        print_info "Please install manually: curl -fsSL https://ollama.ai/install.sh | sh"
        exit 1
    fi
fi

# Start Ollama service (if not running)
print_info "Starting Ollama service..."
if ! pgrep -x ollama > /dev/null 2>&1; then
    # Start Ollama in background
    ollama serve > /dev/null 2>&1 &
    sleep 3
    
    # Verify Ollama is running
    if pgrep -x ollama > /dev/null 2>&1; then
        print_success "Ollama service started"
    else
        print_error "Failed to start Ollama service"
        print_info "You may need to start it manually: ollama serve"
    fi
else
    print_success "Ollama service is already running"
fi

# ============================================================================
# STEP 9: Pull Ollama Model
# ============================================================================
print_step "[9/10] Downloading Ollama model (llama3.2)..."
print_info "This may take a few minutes depending on your internet connection..."

# Wait a bit for Ollama to be ready
sleep 2

# Check if model is already downloaded
if ollama list 2>/dev/null | grep -q "llama3.2"; then
    print_success "Model llama3.2 is already downloaded"
else
    print_info "Downloading llama3.2 model (this may take several minutes)..."
    ollama pull llama3.2
    
    if ollama list 2>/dev/null | grep -q "llama3.2"; then
        print_success "Model llama3.2 downloaded successfully"
    else
        print_error "Failed to download model"
        print_info "You can download it manually later: ollama pull llama3.2"
    fi
fi

# ============================================================================
# STEP 10: Setup Environment File
# ============================================================================
print_step "[10/10] Setting up environment configuration..."

if [ -f ".env" ]; then
    print_info ".env file already exists. Skipping..."
    print_info "If you want to regenerate it, delete .env and run this script again"
else
    if [ -f "config/env.template" ]; then
        # Copy template
        cp config/env.template .env
        
        # Generate secret key
        SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
        
        # Update .env with generated values
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
            sed -i '' "s|LLM_PROVIDER=.*|LLM_PROVIDER=ollama|" .env
            sed -i '' "s|OLLAMA_MODEL=.*|OLLAMA_MODEL=llama3.2|" .env
        else
            # Linux
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
            sed -i "s|LLM_PROVIDER=.*|LLM_PROVIDER=ollama|" .env
            sed -i "s|OLLAMA_MODEL=.*|OLLAMA_MODEL=llama3.2|" .env
        fi
        
        print_success ".env file created with default Ollama configuration"
        print_info "Secret key has been generated automatically"
        print_info "You can edit .env file to add Google OAuth credentials (optional)"
    else
        print_error "config/env.template not found!"
        exit 1
    fi
fi

# ============================================================================
# Setup Complete!
# ============================================================================
print_step "🎉 Setup Complete!"

echo ""
echo -e "${GREEN}✅ All components installed successfully!${NC}"
echo ""
echo "📋 Summary:"
echo "  • Python virtual environment: venv/"
echo "  • Python dependencies: Installed"
echo "  • Ollama: Installed and running"
echo "  • Model llama3.2: Downloaded"
echo "  • Environment file: .env (configured for Ollama)"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. (Optional) Edit .env file to add Google OAuth credentials:"
echo "   nano .env"
echo ""
echo "2. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the application:"
echo "   python run.py"
echo ""
echo "4. Open your browser:"
echo "   http://localhost:5000"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start: UBUNTU_QUICKSTART.md"
echo "   • Full Guide: docs/UBUNTU_SETUP.md"
echo "   • Troubleshooting: docs/troubleshooting/"
echo ""
print_info "Note: Ollama is running in the background. To stop it: pkill ollama"
echo ""
