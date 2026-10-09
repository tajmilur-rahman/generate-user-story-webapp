"""
Flask API server for User Story Automation
Handles document uploads and generates user stories using autoAgile backend
"""
import os
import logging
import tempfile
import sys
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv

# Reconfigure stdout/stderr to UTF-8 on Windows so emoji in log messages don't crash the console handler
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Configure logging
# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Look for .env in project root (two levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Only show .env status if not found
if not os.path.exists(env_path):
    print(f"[WARNING] .env file NOT found at: {env_path}")
    print(f"   Note: .env is optional - will use defaults (Ollama)")

# Add paths to sys.path for backwards compatibility with old imports
# This allows old import statements to still work
sys.path.insert(0, project_root)  # For autoAgile imports
sys.path.insert(0, os.path.join(project_root, 'src'))  # For new backend imports

# Import from new structure
from backend.routes import register_routes
from backend.models import db, run_migrations, User
from backend.routes.auth import init_oauth

def create_app():
    # Configure Flask to serve static files and templates from new locations
    static_folder = os.path.join(project_root, 'src', 'frontend', 'static')
    template_folder = os.path.join(project_root, 'src', 'frontend', 'templates')
    instance_folder = os.path.join(project_root, 'instance')

    app = Flask(__name__,
                static_folder=static_folder,
                static_url_path='/assets',
                template_folder=template_folder,
                instance_path=instance_folder)

    # Behind a reverse proxy or tunnel, the request reaches Flask over plain
    # HTTP on a local port, so url_for(..., _external=True) builds an http://
    # callback. Google rejects a non-HTTPS redirect URI for any host other than
    # localhost, which made OAuth fail with redirect_uri_mismatch while the
    # hostname itself was correct.
    #
    # ProxyFix makes Flask honour X-Forwarded-Proto and X-Forwarded-Host. One
    # trusted hop only: the app binds 127.0.0.1, so the sole client able to set
    # those headers is the proxy on the same machine. Binding 0.0.0.0 with this
    # enabled would let anyone on the network forge the scheme.
    # x_for too: without it every request appears to come from the proxy, so
    # per-address login throttling would lump all clients into one bucket.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    CORS(app)  # Enable CORS for frontend

    # Configuration
    UPLOAD_FOLDER = tempfile.gettempdir()
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    
    # Authentication configuration.
    #
    # The development fallback is a known constant, so anyone who knows it can
    # forge a session cookie. That is acceptable on a laptop and not acceptable
    # anywhere else, so say so loudly rather than failing silently.
    _secret = os.environ.get('SECRET_KEY')
    if not _secret:
        _secret = 'dev-secret-key-change-in-production'
        logger.warning(
            "SECRET_KEY is not set; using the well-known development default. "
            "Session cookies can be forged. Set SECRET_KEY before exposing "
            "this beyond localhost."
        )
    app.config['SECRET_KEY'] = _secret
    
    # Database path in project root/instance directory
    db_path = os.path.join(project_root, 'instance', 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session configuration
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Set SESSION_COOKIE_SECURE=true wherever the app is served over HTTPS (the
    # Tailscale Funnel deployment is), so the session cookie is never sent in
    # clear. Left off by default so plain-http://localhost development works.
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get(
        'SESSION_COOKIE_SECURE', 'false').strip().lower() in ('1', 'true', 'yes', 'on')
    app.config['REMEMBER_COOKIE_SECURE'] = app.config['SESSION_COOKIE_SECURE']
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    # "Keep me signed in" lasts a fortnight: long enough that a survey reviewer
    # coming back over several days is not asked again, short enough to expire
    # well before the accounts stop being needed.
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow localhost/127.0.0.1
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize OAuth
    init_oauth(app)
    
    # Bring an existing database up to the current schema, then create any
    # table that does not exist yet. create_all() alone cannot alter a table
    # that is already there, so the migration has to run first.
    run_migrations(app)
    with app.app_context():
        db.create_all()
        # Only log to file, not console
        logger.debug("Database tables created")
    
    # Register routes
    register_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"[STARTING] User Story Automation Server")
    print(f"{'='*60}")
    print(f"Frontend: http://localhost:{port}")
    print(f"API:      http://localhost:{port}/api")
    print(f"Health:   http://localhost:{port}/api/health")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
