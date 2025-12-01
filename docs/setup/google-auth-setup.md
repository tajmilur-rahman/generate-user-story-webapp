# Google OAuth Setup Instructions

## Overview
Your application now has Google OAuth authentication! Users must sign in with their Google account to use the app.

## 🔑 Get Google OAuth Credentials

Before running the app, you need to obtain Google OAuth credentials:

### Step 1: Go to Google Cloud Console
Visit [Google Cloud Console](https://console.cloud.google.com/)

### Step 2: Create or Select a Project
- Click on the project dropdown at the top
- Create a new project or select an existing one

### Step 3: Enable Google+ API
- Go to "APIs & Services" → "Library"
- Search for "Google+ API" or "Google Identity"
- Click "Enable"

### Step 4: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in application name: "User Story Automation"
   - Add your email as developer contact
   - Save and continue through the screens
4. Back in Create OAuth client ID:
   - Application type: **Web application**
   - Name: "User Story Automation"
   - Authorized redirect URIs: Add `http://localhost:5000/auth/callback`
   - Click "Create"
5. **Copy the Client ID and Client Secret** (you'll need these next!)

## 📝 Configure Environment Variables

1. Open the `.env` file in your project root
2. Add your Google OAuth credentials:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here    # Paste your Client ID
GOOGLE_CLIENT_SECRET=your_google_client_secret_here    # Paste your Client Secret

# This secret key has already been generated for you
SECRET_KEY=3ec8ffdebd7291f7f9f21a64ae5b2273ae442f7a6e4
```

3. Save the `.env` file

## 📦 Install New Dependencies

Run this command to install the new authentication packages:

```bash
pip install Flask-Login Authlib Flask-SQLAlchemy
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## 🚀 Run the Application

1. **Stop the current server** (if running) - Press `Ctrl+C` in the terminal
2. **Start the server again**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   - Open your browser and go to `http://localhost:5000`
   - You'll be redirected to the login page
   - Click "Sign in with Google"
   - Complete the Google OAuth flow
   - You'll be redirected back to the app!

## ✅ What's Been Added

### Backend Changes
- ✅ Google OAuth authentication with Authlib
- ✅ User model and SQLite database for storing user sessions
- ✅ Protected API endpoints (requires login)
- ✅ Session management with Flask-Login
- ✅ Authentication routes: `/auth/login`, `/auth/google`, `/auth/callback`, `/auth/logout`

### Frontend Changes
- ✅ Beautiful login page with Google Sign-In button
- ✅ User profile display in navbar with avatar and name
- ✅ Logout button
- ✅ Automatic redirect to login for unauthenticated users

### Security
- ✅ All API endpoints now require authentication
- ✅ Secure session management with HttpOnly cookies
- ✅ User data stored in local SQLite database
- ✅ OAuth 2.0 secure authentication flow

## 🔒 Protected Endpoints

These API endpoints now require authentication:
- `/api/generate-stories` - Generate user stories
- `/api/integrate-story` - Integrate single story
- `/api/integrate-all` - Integrate all stories

## 🐛 Troubleshooting

### "Failed to fetch" error
- Make sure the Flask server is running
- Check that Google OAuth credentials are correct in `.env`

### "Redirect URI mismatch" error
- Go back to Google Cloud Console
- Verify the redirect URI is exactly: `http://localhost:5000/auth/callback`
- Make sure there are no extra spaces or trailing slashes

### Database errors
- The SQLite database (`users.db`) will be created automatically
- If you encounter issues, delete `users.db` and restart the server

## 📚 Next Steps

1. **Add your Google OAuth credentials to `.env`**
2. **Install the new dependencies**
3. **Restart the server**
4. **Test the login flow**

Enjoy your secure, authenticated user story automation app! 🎉
