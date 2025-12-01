from flask import Blueprint, render_template

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@frontend_bp.route('/stories.html')
def stories():
    """Serve the stories page"""
    return render_template('stories.html')

@frontend_bp.route('/login.html')
def login():
    """Serve the login page"""
    return render_template('login.html')

@frontend_bp.route('/favicon.ico')
def favicon():
    """Handle favicon requests (suppress 404 errors)"""
    return '', 204
