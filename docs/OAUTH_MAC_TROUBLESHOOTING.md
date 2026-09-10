# OAuth Troubleshooting Guide for Mac

This guide addresses common OAuth authentication issues on macOS.

---

## 🔴 Common Issues & Solutions

### **1. Redirect URI Mismatch** (Most Common)

**Symptoms**:
- "Error 400: redirect_uri_mismatch" in browser
- OAuth callback fails with "The redirect URI in the request did not match a registered redirect URI"

**Cause**: Mac treats `localhost` and `127.0.0.1` as different hosts.

**Solution**:

#### A. Configure Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add **BOTH**:
   ```
   http://localhost:5000/auth/callback
   http://127.0.0.1:5000/auth/callback
   ```
4. Click **Save**

#### B. Force localhost in Flask

Add to your `.env` file:
```env
# Force Flask to use localhost (not 127.0.0.1)
SERVER_NAME=localhost:5000
```

**Or** when running Flask:
```bash
python src/backend/app.py --host=localhost
```

---

### **2. Safari Cookie Blocking**

**Symptoms**:
- Successful OAuth redirect but user not logged in
- Session immediately expires after login
- "Login required" error after OAuth callback

**Cause**: Safari blocks third-party cookies and has strict SameSite policies.

**Solutions**:

#### A. Disable Safari Privacy Features (Testing Only)

1. Open Safari → Settings/Preferences
2. Go to **Privacy** tab
3. **Uncheck** "Prevent cross-site tracking"
4. **Uncheck** "Block all cookies"
5. Restart Safari

#### B. Use Chrome/Firefox Instead (Recommended)

Safari's privacy features can interfere with OAuth. Use Chrome or Firefox for development:

```bash
# Set Chrome as default browser temporarily
open -a "Google Chrome" http://localhost:5000
```

#### C. Session Cookie Fix (Already Applied)

The session cookie settings have been updated in `app.py` to:
```python
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP cookies
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow localhost/127.0.0.1
```

---

### **3. Port 5000 Already in Use**

**Symptoms**:
- "Address already in use" error
- Flask won't start

**Cause**: Mac uses port 5000 for AirPlay Receiver (macOS Monterey+)

**Solutions**:

#### A. Disable AirPlay Receiver

1. **System Settings** → **General** → **AirDrop & Handoff**
2. Turn OFF **AirPlay Receiver**

#### B. Use Different Port

In `.env`:
```env
PORT=5001
```

Then access at: `http://localhost:5001`

**Important**: Update Google OAuth redirect URIs:
```
http://localhost:5001/auth/callback
http://127.0.0.1:5001/auth/callback
```

---

### **4. HTTPS Required Error**

**Symptoms**:
- "redirect_uri must use HTTPS" error
- OAuth provider rejects HTTP callback

**Cause**: Some OAuth providers require HTTPS in production settings.

**Solution** (Development):

Use `ngrok` to create HTTPS tunnel:

```bash
# Install ngrok
brew install ngrok

# Create tunnel
ngrok http 5000

# Output: https://abc123.ngrok.io
```

Update Google OAuth redirect URI:
```
https://abc123.ngrok.io/auth/callback
```

Update `.env`:
```env
# Tell Flask it's behind HTTPS proxy
PREFERRED_URL_SCHEME=https
```

---

### **5. Environment Variables Not Loading**

**Symptoms**:
- "GOOGLE_CLIENT_ID not configured" error
- OAuth credentials not found

**Cause**: `.env` file not in correct location or not loaded.

**Solutions**:

#### A. Verify .env Location

```bash
# Must be in project root
ls -la /path/to/user-story-automation/.env
```

#### B. Check .env is Loading

Add debug print to `app.py`:
```python
load_dotenv(dotenv_path=env_path)
print(f"GOOGLE_CLIENT_ID: {os.environ.get('GOOGLE_CLIENT_ID')}")  # Debug
```

#### C. Export Variables Manually (Testing)

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-secret"
python src/backend/app.py
```

---

### **6. Flask Session Persists Across Restarts**

**Symptoms**:
- Old session data causes errors
- Login state inconsistent

**Solution**:

Clear Flask session and database:

```bash
# Remove session files
rm -rf flask_session/

# Remove database
rm instance/users.db

# Restart server
python src/backend/app.py
```

---

### **7. Mac Firewall Blocking Localhost**

**Symptoms**:
- Can't access `http://localhost:5000`
- Connection refused errors

**Solution**:

#### A. Check Firewall Settings

1. **System Settings** → **Network** → **Firewall**
2. If ON, click **Firewall Options**
3. Make sure Python is **allowed** to accept incoming connections

#### B. Temporarily Disable Firewall (Testing)

```bash
# Disable (requires admin)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off

# Re-enable after testing
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
```

---

### **8. Browser Cache Issues**

**Symptoms**:
- Old OAuth tokens cached
- Login page shows stale data

**Solution**:

```bash
# Clear browser cache
# Chrome: Cmd+Shift+Delete → Clear browsing data
# Safari: Cmd+Option+E → Empty Caches

# Or use private/incognito mode
```

---

## ✅ Complete Checklist

Use this checklist to diagnose OAuth issues:

- [ ] **Google Cloud Console**: Both `localhost` and `127.0.0.1` redirect URIs added
- [ ] **Browser**: Using Chrome/Firefox (not Safari)
- [ ] **Port 5000**: Available (AirPlay Receiver disabled if needed)
- [ ] **.env file**: In project root with correct credentials
- [ ] **Flask server**: Running without errors (`python src/backend/app.py`)
- [ ] **Cookies enabled**: Browser allows cookies from localhost
- [ ] **Firewall**: Python allowed to accept connections
- [ ] **Clear cache**: Browser cache cleared or using incognito

---

## 🧪 Test OAuth Flow

### 1. Start Server

```bash
cd /path/to/user-story-automation
python src/backend/app.py
```

Expected output:
```
[STARTING] User Story Automation Server
Frontend: http://localhost:5000
```

### 2. Test Login

Open browser:
```
http://localhost:5000/auth/login
```

Click "Sign in with Google"

### 3. Check Logs

Watch server logs:
```
Redirecting to Google OAuth with callback: http://localhost:5000/auth/callback
User authenticated: your-email@gmail.com
New user created: your-email@gmail.com
```

### 4. Verify Session

Check session endpoint:
```bash
curl http://localhost:5000/auth/status
```

Expected:
```json
{
  "authenticated": true,
  "user": {
    "email": "your-email@gmail.com",
    "name": "Your Name"
  }
}
```

---

## 🐛 Debug Mode

Enable detailed logging:

```python
# In app.py, add before app.run():
logging.getLogger('authlib').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
```

Then check logs for detailed OAuth flow:
```bash
tail -f data/logs/app.log
```

---

## 🆘 Still Having Issues?

### Collect Debug Information

```bash
# 1. Check .env
cat .env | grep -E "GOOGLE|GITHUB|PORT"

# 2. Check Python/Flask versions
python --version
pip list | grep -E "Flask|authlib"

# 3. Check running processes
lsof -i :5000

# 4. Check server logs
tail -50 data/logs/app.log

# 5. Test OAuth redirect manually
curl -v http://localhost:5000/auth/google
```

### Common Error Messages

**"redirect_uri_mismatch"**
→ Fix: Add both localhost and 127.0.0.1 to Google Console

**"invalid_client"**
→ Fix: Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env

**"Session cookie not set"**
→ Fix: Enable cookies in browser, or use Chrome/Firefox

**"Port 5000 already in use"**
→ Fix: Disable AirPlay Receiver or use PORT=5001

---

## 📚 Resources

- [Google OAuth Setup Guide](https://developers.google.com/identity/protocols/oauth2)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Authlib Documentation](https://docs.authlib.org/)
- [Mac AirPlay Port Issue](https://developer.apple.com/forums/thread/682332)

---

## 🔧 Quick Fix Script

Save as `fix-oauth-mac.sh`:

```bash
#!/bin/bash
echo "🔧 Fixing OAuth issues on Mac..."

# 1. Kill any process on port 5000
echo "Killing processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# 2. Clear Flask session
echo "Clearing Flask session..."
rm -rf flask_session/

# 3. Remove old database
echo "Removing old database..."
rm -f instance/users.db

# 4. Check .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    exit 1
fi

echo "✅ Ready to start Flask server"
echo "Run: python src/backend/app.py"
```

Run with:
```bash
chmod +x fix-oauth-mac.sh
./fix-oauth-mac.sh
```

---

**Need more help?** Check the main logs at `data/logs/app.log` or open a GitHub issue.
