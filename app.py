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
