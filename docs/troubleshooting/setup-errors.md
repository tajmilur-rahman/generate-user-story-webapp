# Setup Script Troubleshooting

This guide helps resolve common errors encountered during the setup script execution.

## MySQL Installation Errors

### Error Message
```
subprocess returned a non-zero exit code 1
/usr/bin/dpkg
errors were encountered while processing mysql-server-8.0
```

### Cause
This error occurs when MySQL packages are in a broken or partially installed state, blocking other package installations.

### Solution

#### Option 1: Fix Broken Packages (Recommended)
```bash
# Fix all broken packages
sudo dpkg --configure -a

# Fix broken dependencies
sudo apt --fix-broken install -y

# Update package lists
sudo apt update

# Retry the setup script
bash scripts/setup/setup.sh
```

#### Option 2: Remove MySQL (If Not Needed)
If you don't need MySQL for other projects:

```bash
# Remove MySQL completely
sudo apt remove --purge mysql-server mysql-common mysql-client-* -y
sudo apt autoremove -y
sudo apt autoclean

# Fix any remaining broken packages
sudo dpkg --configure -a
sudo apt --fix-broken install -y

# Retry the setup script
bash scripts/setup/setup.sh
```

#### Option 3: Reinstall MySQL (If You Need It)
If you need MySQL for other projects:

```bash
# Remove broken MySQL installation
sudo apt remove --purge mysql-server mysql-common mysql-client-* -y

# Clean up
sudo apt autoremove -y
sudo apt autoclean

# Reinstall MySQL properly (optional, only if needed)
sudo apt update
sudo apt install mysql-server -y

# Retry the setup script
bash scripts/setup/setup.sh
```

## Python 3.11 Not Found

### Error Message
```
E: Unable to locate package python3.11
```

### Solution
The updated setup script should handle this automatically by adding the deadsnakes PPA. If it still fails:

```bash
# Manually add the PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Retry the setup script
bash scripts/setup/setup.sh
```

## Permission Denied Errors

### Error Message
```
Permission denied
```

### Solution
Make sure the script is executable and you're not running as root:

```bash
# Make script executable
chmod +x scripts/setup/setup.sh

# Run as regular user (not root)
bash scripts/setup/setup.sh
```

The script will ask for sudo password when needed.

## General Package Installation Failures

### Solution
```bash
# Clean package cache
sudo apt clean
sudo apt autoclean

# Update package lists
sudo apt update

# Fix broken packages
sudo dpkg --configure -a
sudo apt --fix-broken install -y

# Retry the setup script
bash scripts/setup/setup.sh
```

## Still Having Issues?

1. Check the full error message in the terminal
2. Review the setup script logs
3. Try running individual steps manually
4. Check system logs: `sudo tail -f /var/log/dpkg.log`
5. Ensure you have internet connectivity
6. Verify you have sufficient disk space: `df -h`
