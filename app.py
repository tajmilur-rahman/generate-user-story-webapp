"""
Flask API server for User Story Automation
Handles document uploads and generates user stories using autoAgile backend
"""
import os
import logging
import tempfile
import sys
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

if os.path.exists(env_path):
    print(f"[OK] .env file found: {env_path}")
else:
    print(f"[WARNING] .env file NOT found at: {env_path}")
    print(f"   Note: .env is optional - will use defaults (Ollama)")

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from routes import register_routes
from database import db, init_db
from models import User
from routes.auth import init_oauth

def create_app():
    # Configure Flask to serve static files and templates
    app = Flask(__name__, 
                static_folder='assets',
                static_url_path='/assets',
                template_folder='pages')
    CORS(app)  # Enable CORS for frontend

    # Configuration
    UPLOAD_FOLDER = tempfile.gettempdir()
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    
    # Authentication configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session configuration
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
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
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("[OK] Database tables created")
    
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
