# SMTP Email Configuration

This guide explains how to configure SMTP email functionality for sending welcome emails to new users.

## Overview

When a user logs in for the first time (via Google OAuth), the system automatically sends them a welcome email. This feature requires SMTP configuration.

## Environment Variables

Add the following environment variables to your `.env` file:

```bash
# SMTP Server Configuration
SMTP_SERVER=smtp.gmail.com          # SMTP server address (Gmail, Outlook, etc.)
SMTP_PORT=587                       # SMTP port (587 for TLS, 465 for SSL)
SMTP_USERNAME=your-email@gmail.com  # Your email address
SMTP_PASSWORD=your-app-password     # Your email password or app password
SMTP_FROM_EMAIL=your-email@gmail.com # Sender email (defaults to SMTP_USERNAME)
SMTP_FROM_NAME=User Story Automation # Sender name
SMTP_USE_TLS=true                   # Use TLS encryption (true/false)
```

## Gmail Setup

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Enable 2-Factor Authentication

### Step 2: Generate App Password
1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Custom name)"
3. Enter "User Story Automation" as the name
4. Click "Generate"
5. Copy the 16-character password (use this as `SMTP_PASSWORD`)

### Step 3: Configure .env File
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-character app password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=User Story Automation
SMTP_USE_TLS=true
```

## Outlook/Office 365 Setup

```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@outlook.com
SMTP_FROM_NAME=User Story Automation
SMTP_USE_TLS=true
```

## Other SMTP Providers

### SendGrid
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=your-verified-email@domain.com
SMTP_FROM_NAME=User Story Automation
SMTP_USE_TLS=true
```

### Mailgun
```bash
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-username
SMTP_PASSWORD=your-mailgun-password
SMTP_FROM_EMAIL=your-verified-email@domain.com
SMTP_FROM_NAME=User Story Automation
SMTP_USE_TLS=true
```

## Testing

1. Start the application
2. Log in with a new Google account (first-time login)
3. Check the application logs for email sending status
4. Check the user's email inbox for the welcome email

## Troubleshooting

### Email Not Sending
- Check that all SMTP environment variables are set correctly
- Verify SMTP credentials are correct
- Check application logs for error messages
- Ensure firewall allows outbound connections on SMTP port

### Gmail "Less Secure App" Error
- Use App Passwords instead of regular password
- Ensure 2-Factor Authentication is enabled

### Connection Timeout
- Check if SMTP port is blocked by firewall
- Try different SMTP port (587 for TLS, 465 for SSL)
- Verify SMTP server address is correct

## Disabling Email

If you don't want to send emails, simply don't set the `SMTP_USERNAME` and `SMTP_PASSWORD` environment variables. The application will log a warning but continue to function normally.

## Email Template

The welcome email includes:
- Personalized greeting with user's name
- Information about platform features
- Styled HTML template
- Plain text fallback

The email template can be customized in `src/backend/services/email_service.py` in the `send_welcome_email()` method.

