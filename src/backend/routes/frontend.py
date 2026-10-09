from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from backend.features import github_integration_enabled

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
@login_required
def index():
    """
    Serve the main index page.

    Gated server-side. The page's own script also checks /auth/status and
    redirects, but that runs after the markup has already been delivered, so it
    hides the app rather than protecting it.
    """
    return render_template('index.html')

@frontend_bp.route('/stories.html')
@login_required
def stories():
    """Serve the stories page"""
    return render_template('stories.html',
                           show_github_integration=github_integration_enabled())

@frontend_bp.route('/login.html')
def login():
    """
    Legacy path for the login page.

    Redirects rather than rendering a second copy: the real page at
    /auth/login issues the CSRF token the form needs, so a bare render here
    would produce a form that always fails.
    """
    return redirect(url_for('auth.login'))

@frontend_bp.route('/favicon.ico')
def favicon():
    """Handle favicon requests (suppress 404 errors)"""
    return '', 204
