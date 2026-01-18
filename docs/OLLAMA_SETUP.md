# Ollama Setup Guide - After Installation

This guide explains what to do after installing Ollama from the official website.

## Step 1: Verify Ollama Installation

Open a terminal/command prompt and check if Ollama is installed:

```bash
ollama --version
```

You should see something like: `ollama version is 0.x.x`

If you get "command not found" or "ollama is not recognized":
- **Windows**: Restart your terminal/command prompt after installation
- **macOS/Linux**: Make sure Ollama is in your PATH, or restart terminal

## Step 2: Start Ollama Service

Ollama needs to be running as a service to handle LLM requests.

### Windows:
Ollama usually starts automatically after installation. If not:
1. Open Ollama from Start Menu, or
2. Run in terminal: `ollama serve`

### macOS/Linux:
```bash
ollama serve
```

**Keep this terminal window open** - Ollama needs to keep running.

You should see:
```
INFO[0000] server config env="map[OLLAMA_HOST:0.0.0.0:11434]"
INFO[0000] starting server...
```

## Step 3: Download a Model

In a **new terminal window** (keep Ollama running in the first one), download a model:

### Recommended Models:

**Option 1: llama3.2 (Recommended - Balanced)**
```bash
ollama pull llama3.2
```

**Option 2: mistral (Fast and Efficient)**
```bash
ollama pull mistral
```

**Option 3: qwen2.5 (Multilingual Support)**
```bash
ollama pull qwen2.5
```

The download will take a few minutes depending on your internet speed. Models are typically 2-7 GB in size.

## Step 4: Verify Model is Downloaded

Check which models you have:

```bash
ollama list
```

You should see your downloaded model listed, for example:
```
NAME            ID              SIZE    MODIFIED
llama3.2        abc123def456    4.7 GB  2 hours ago
```

## Step 5: Test Ollama is Working

Test that Ollama can generate responses:

```bash
ollama run llama3.2 "Hello, can you respond?"
```

You should get a response from the model. Type `exit` or press Ctrl+C to exit.

## Step 6: Configure Your Project

### Update .env File

Make sure your `.env` file has these settings:

```bash
# LLM Provider
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Replace `llama3.2` with the model you downloaded (e.g., `mistral`, `qwen2.5`).

## Step 7: Test with Your Application

1. **Make sure Ollama is running:**
   ```bash
   # In one terminal
   ollama serve
   ```

2. **Start your application:**
   ```bash
   # In another terminal
   cd "C:\Users\avish\OneDrive\Desktop\User-story\user-story-automation"
   venv\Scripts\activate  # Activate virtual environment
   python run.py
   ```

3. **Test the health endpoint:**
   - Open browser: http://localhost:5000/api/health
   - You should see Ollama status and model information

## Common Issues

### Ollama Not Starting

**Problem:** `ollama serve` doesn't work

**Solutions:**
- **Windows**: Restart your computer after installation
- Check if Ollama is already running: Look for Ollama in Task Manager (Windows) or Activity Monitor (macOS)
- Try running as administrator (Windows) or with sudo (Linux)

### Model Download Fails

**Problem:** `ollama pull` fails or is very slow

**Solutions:**
- Check your internet connection
- Try a smaller model first: `ollama pull tinyllama` (for testing)
- Check disk space (models need several GB)
- Try again later if servers are busy

### Application Can't Connect to Ollama

**Problem:** Application shows "Ollama not available" or connection errors

**Solutions:**
1. **Verify Ollama is running:**
   ```bash
   # Check if Ollama is responding
   curl http://localhost:11434/api/tags
   ```
   Should return JSON with model list

2. **Check OLLAMA_BASE_URL in .env:**
   - Should be: `OLLAMA_BASE_URL=http://localhost:11434`
   - No trailing slash

3. **Check firewall settings:**
   - Make sure port 11434 is not blocked
   - Windows Firewall may need to allow Ollama

4. **Verify model name:**
   - Model name in `.env` must match exactly what you downloaded
   - Check with: `ollama list`

### Model Not Found Error

**Problem:** Application says model not found

**Solution:**
1. Check model name in `.env` matches downloaded model
2. Verify model is downloaded: `ollama list`
3. Pull the model again: `ollama pull llama3.2`

## Quick Reference Commands

```bash
# Check Ollama version
ollama --version

# Start Ollama service
ollama serve

# List downloaded models
ollama list

# Download a model
ollama pull llama3.2

# Test a model
ollama run llama3.2 "Your question here"

# Remove a model (to free space)
ollama rm llama3.2
```

## Next Steps

After Ollama is set up:

1. ✅ Ollama is installed and verified
2. ✅ Ollama service is running (`ollama serve`)
3. ✅ Model is downloaded (`ollama pull llama3.2`)
4. ✅ .env file is configured
5. ✅ Application can connect to Ollama

You're ready to use the application! Start generating user stories.

## Performance Tips

- **For faster responses**: Use `mistral` model (smaller, faster)
- **For better quality**: Use `llama3.2` or larger models
- **For testing**: Use `tinyllama` (very small, fast, but lower quality)
- **Memory**: Models use RAM while running, close other applications if needed

## Troubleshooting

If you encounter issues:

1. **Check Ollama logs:**
   - Look at the terminal where `ollama serve` is running
   - Check for error messages

2. **Restart Ollama:**
   - Stop: Press Ctrl+C in the terminal running `ollama serve`
   - Start: Run `ollama serve` again

3. **Check application logs:**
   - Look in `data/logs/app.log` for error messages
   - Check console output when running the application

4. **Verify configuration:**
   - Double-check `.env` file settings
   - Make sure model name matches exactly

## Need Help?

- Ollama Documentation: https://github.com/ollama/ollama
- Ollama Models: https://ollama.ai/library
- Check application logs: `data/logs/app.log`

