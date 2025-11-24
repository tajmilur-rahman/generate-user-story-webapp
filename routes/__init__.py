from .api import api_bp
from .frontend import frontend_bp

def register_routes(app):
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(frontend_bp)
