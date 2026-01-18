# Cross-Platform Compatibility

This application is fully compatible with Ubuntu Linux, Windows, and macOS.

## ✅ Cross-Platform Features

### File Paths
- ✅ All file paths use `os.path.join()` for cross-platform compatibility
- ✅ No hardcoded Windows paths (C:\, backslashes, etc.)
- ✅ Upload directory uses `tempfile.gettempdir()` (works on all platforms)

### Python Code
- ✅ Pure Python - no platform-specific code
- ✅ All dependencies are cross-platform
- ✅ Database uses SQLite (works everywhere)

### Configuration
- ✅ Environment variables work the same on all platforms
- ✅ `.env` file format is platform-independent

## Platform-Specific Setup

### Ubuntu/Linux
```bash
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh
source venv/bin/activate
python run.py
```

### Windows
```bash
.\scripts\setup\setup.ps1
# Or
scripts\setup\setup.bat
venv\Scripts\activate
python run.py
```

### macOS
```bash
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh
source venv/bin/activate
python run.py
```

## File Path Differences

| Platform | Temp Directory | Virtual Env Activation |
|----------|--------------|------------------------|
| Ubuntu/Linux | `/tmp` | `source venv/bin/activate` |
| Windows | `C:\Users\...\AppData\Local\Temp` | `venv\Scripts\activate` |
| macOS | `/tmp` | `source venv/bin/activate` |

The application automatically handles these differences using Python's `os.path` and `tempfile` modules.

## Scripts

### Linux/Ubuntu/macOS
- `scripts/setup/setup.sh` - Setup script
- `scripts/start.sh` - Start server
- `scripts/stop.sh` - Stop server
- `scripts/force-stop.sh` - Force stop

### Windows
- `scripts/setup/setup.bat` - Batch setup script
- `scripts/setup/setup.ps1` - PowerShell setup script

## Dependencies

All Python dependencies in `requirements.txt` are cross-platform:
- ✅ flask
- ✅ flask-cors
- ✅ python-docx
- ✅ langchain-* (all variants)
- ✅ python-dotenv
- ✅ werkzeug
- ✅ Flask-Login
- ✅ Authlib
- ✅ Flask-SQLAlchemy

## Testing on Ubuntu

To verify Ubuntu compatibility:

```bash
# 1. Check Python version
python3 --version  # Should be 3.11+

# 2. Run setup
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh

# 3. Test imports
source venv/bin/activate
python -c "from src.backend.app import app; print('✅ App imports successfully')"

# 4. Run application
python run.py
```

## Known Platform Differences

### Line Endings
- Windows uses `\r\n` (CRLF)
- Linux/Ubuntu uses `\n` (LF)
- ✅ Python handles this automatically

### File Permissions
- Linux/Ubuntu: Scripts need `chmod +x` to be executable
- Windows: Scripts are executable by default
- ✅ Setup scripts handle this

### Path Separators
- Windows: `\` (backslash)
- Linux/Ubuntu: `/` (forward slash)
- ✅ `os.path.join()` handles this automatically

## Troubleshooting

### Ubuntu-Specific Issues

**Permission Denied:**
```bash
chmod +x scripts/setup/setup.sh
chmod +x scripts/*.sh
```

**Python Command Not Found:**
```bash
# Use python3 explicitly
python3 run.py

# Or create alias
alias python=python3
```

**Port Already in Use:**
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

## Verification Checklist

- [x] All file paths use `os.path.join()`
- [x] No hardcoded Windows paths
- [x] Virtual environment activation scripts for both platforms
- [x] Setup scripts for both platforms
- [x] Cross-platform dependencies
- [x] Database uses SQLite (cross-platform)
- [x] Upload directory uses `tempfile.gettempdir()`
- [x] Environment variables work the same
- [x] Documentation updated for Ubuntu

## Summary

The application is **fully Ubuntu-compatible** and ready to run on Linux systems. All platform-specific differences are handled automatically by Python's standard library.
