"""
Main application launcher.
Imports and runs the Flask app from the new src/backend structure.
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the app from the new location
from backend.app import app

if __name__ == '__main__':
    # use_reloader=False prevents Flask from watching Python stdlib files
    # (json/__init__.py, logging/__init__.py etc.) and restarting mid-request
    # which caused ERR_CONNECTION_RESET in the browser.
    # After changing backend code, just stop and restart the server manually.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
