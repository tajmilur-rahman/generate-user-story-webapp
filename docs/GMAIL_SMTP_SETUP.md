# How to Enable Gmail SMTP for Email Sending

This guide walks you through enabling Gmail SMTP to send welcome emails when users log in for the first time.

## Prerequisites

- A Gmail account
- Access to your Google Account settings

## Step-by-Step Instructions

### Step 1: Enable 2-Factor Authentication (Required)

1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Under "How you sign in to Google", find **2-Step Verification**
4. Click **Get started** and follow the prompts to enable 2-Factor Authentication
   - You'll need to verify your phone number
   - You may need to enter a verification code sent to your phone

**Why this is required:** Google requires 2FA to be enabled before you can generate App Passwords for SMTP.

### Step 2: Generate an App Password

1. Go to **App Passwords** page: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → 2-Step Verification → App passwords

2. You may need to sign in again to verify your identity

3. Under "Select app", choose **Mail**

4. Under "Select device", choose **Other (Custom name)**

5. Type: `User Story Automation` (or any name you prefer)

6. Click **Generate**

7. Google will show you a **16-character password** that looks like:
   ```
   xxxx xxxx xxxx xxxx
   ```
   **Important:** Copy this password immediately - you won't be able to see it again!

### Step 3: Update Your .env File

1. Open your `.env` file in the project root directory

2. Update the SMTP configuration with your Gmail credentials:

```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-actual-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_EMAIL=your-actual-email@gmail.com
SMTP_FROM_NAME=User Story Automation
SMTP_USE_TLS=true
```

**Replace:**
- `your-actual-email@gmail.com` → Your actual Gmail address
- `xxxx xxxx xxxx xxxx` → The 16-character App Password you just generated
  - You can include or remove the spaces - both work

### Step 4: Test the Configuration

1. **Restart your Flask application** to load the new environment variables

2. **Check the logs** when the app starts - you should see:
   ```
   [INFO] SMTP configured successfully
   ```
   Or if not configured:
   ```
   [WARNING] SMTP not configured. Email functionality will be disabled.
   ```

3. **Test with a new user login:**
   - Log in with a Google account that hasn't logged in before
   - Check the application logs for: `Welcome email sent to [email]`
   - Check the user's email inbox for the welcome message

## Troubleshooting

### "Username and Password not accepted" Error

**Problem:** Gmail is rejecting your credentials

**Solutions:**
1. **Make sure you're using an App Password, not your regular Gmail password**
   - Regular passwords won't work with SMTP
   - You must use the 16-character App Password

2. **Check that 2-Factor Authentication is enabled**
   - App Passwords only work when 2FA is enabled

3. **Verify the App Password is correct**
   - Copy it exactly as shown (spaces don't matter)
   - Make sure there are no extra spaces

4. **Try regenerating the App Password**
   - Delete the old one and create a new one

### "Less secure app access" Error

**Problem:** Google is blocking the connection

**Solution:** This shouldn't happen with App Passwords, but if it does:
- Make sure you're using an App Password (not regular password)
- Check that 2FA is enabled
- Try using port 465 with SSL instead of TLS

### Email Not Sending

**Check the application logs:**
```bash
# Look for these log messages:
[INFO] Welcome email sent to user@example.com
[ERROR] SMTP error sending email...
[WARNING] SMTP not configured...
```

**Common issues:**
1. SMTP credentials not set in `.env` file
2. Wrong SMTP server/port
3. Firewall blocking SMTP port 587
4. Gmail blocking the connection

### Connection Timeout

**Problem:** Can't connect to Gmail SMTP server

**Solutions:**
1. Check your internet connection
2. Verify firewall allows outbound connections on port 587
3. Try port 465 with SSL (change `SMTP_USE_TLS=false` and port to 465)
4. Check if your network blocks SMTP ports

## Alternative: Using Other Email Providers

If Gmail doesn't work for you, you can use:

### Outlook/Office 365
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
```

### SendGrid
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

See `docs/SMTP_EMAIL_SETUP.md` for more providers.

## Security Best Practices

1. **Never commit `.env` file to Git**
   - It contains sensitive credentials
   - Already in `.gitignore`

2. **Use App Passwords, not regular passwords**
   - More secure
   - Can be revoked individually

3. **Rotate App Passwords periodically**
   - Delete old ones and create new ones

4. **Use environment variables in production**
   - Don't hardcode credentials in code

## Quick Reference

| Setting | Value |
|---------|-------|
| SMTP Server | `smtp.gmail.com` |
| Port | `587` (TLS) or `465` (SSL) |
| Username | Your Gmail address |
| Password | 16-character App Password |
| TLS/SSL | `true` for port 587, `false` for port 465 |

## Need Help?

- Check application logs for detailed error messages
- See `docs/SMTP_EMAIL_SETUP.md` for more configuration options
- Verify your `.env` file has all SMTP variables set correctly

