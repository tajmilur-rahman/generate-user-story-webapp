from .api import api_bp
from .frontend import frontend_bp
from .auth import auth_bp

def register_routes(app):
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(frontend_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
