"""
Routes package - handles all HTTP endpoints
"""
from .frontend import frontend_bp
from .auth import auth_bp
from .api import api_bp
from .api_agentic import api_agentic_bp

def register_routes(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_agentic_bp, url_prefix='/api/agentic')
    app.register_blueprint(frontend_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
