from flask import Blueprint, send_from_directory

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Serve the main index page"""
    return send_from_directory('pages', 'index.html')

@frontend_bp.route('/stories.html')
def stories():
    """Serve the stories page"""
    return send_from_directory('pages', 'stories.html')

@frontend_bp.route('/favicon.ico')
def favicon():
    """Handle favicon requests (suppress 404 errors)"""
    return '', 204
