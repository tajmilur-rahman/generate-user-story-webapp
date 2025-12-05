"""
Authentication routes for Google OAuth
"""
import os
import logging
from flask import Blueprint, redirect, url_for, session, request, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from datetime import datetime
from backend.models import User, db
from backend.services.email_service import email_service

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    
    # Register Google OAuth provider
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.debug("Google OAuth initialized")

@auth_bp.route('/login')
def login():
    """Render login page"""
    # If user is already logged in, redirect to index
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('login.html')

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth flow"""
    redirect_uri = url_for('auth.google_callback', _external=True)
    logger.info(f"Redirecting to Google OAuth with callback: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Get access token from Google
        token = oauth.google.authorize_access_token()
        
        # Get user info from Google
        user_info = token.get('userinfo')
        
        if not user_info:
            logger.error("Failed to get user info from Google")
            return redirect(url_for('auth.login'))
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        logger.info(f"User authenticated: {email}")
        
        # Find or create user in database
        user = User.query.filter_by(google_id=google_id).first()
        is_new_user = False
        
        if not user:
            # Create new user (first-time login)
            is_new_user = True
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            db.session.add(user)
            logger.info(f"New user created: {email}")
        else:
            # Update existing user info
            user.name = name
            user.picture = picture
            user.last_login = datetime.utcnow()
            logger.info(f"Existing user logged in: {email}")
        
        db.session.commit()
        
        # Send welcome email for first-time login
        if is_new_user:
            try:
                user_display_name = name or email.split('@')[0]
                email_sent = email_service.send_welcome_email(email, user_display_name)
                if email_sent:
                    logger.info(f"Welcome email sent to {email}")
                else:
                    logger.warning(f"Failed to send welcome email to {email} (SMTP may not be configured)")
            except Exception as e:
                # Don't fail login if email fails
                logger.error(f"Error sending welcome email to {email}: {e}")
        
        # Log user in with Flask-Login
        login_user(user)
        
        # Redirect to index page
        return redirect('/')
        
    except Exception as e:
        logger.error(f"Error in Google callback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out user"""
    logger.info(f"User logged out: {current_user.email}")
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/user')
def get_user():
    """Get current user information"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    else:
        return jsonify({
            'authenticated': False
        })

@auth_bp.route('/status')
def auth_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user': current_user.to_dict() if current_user.is_authenticated else None
    })
