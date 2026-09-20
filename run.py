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



def _env_flag(name, default=False):
    """Read a boolean environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


if __name__ == '__main__':
    # Debug defaults to OFF. debug=True serves the Werkzeug interactive
    # debugger, and combined with host 0.0.0.0 that is remote code execution for
    # anyone who can reach the port and trigger a traceback. Enable it
    # deliberately with FLASK_DEBUG=1, and only on a trusted network.
    debug = _env_flag('FLASK_DEBUG', default=False)
    host = os.environ.get('FLASK_HOST', '127.0.0.1' if not debug else '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))

    if debug:
        print("WARNING: debug mode is ON. The interactive debugger can execute "
              "code. Never expose this beyond localhost.")

    print(f"Development server on http://{host}:{port} (debug={debug})")
    print("This is NOT a production server. See docs/DEPLOYMENT.md to serve "
          "with gunicorn (Linux) or waitress (Windows).")

    # use_reloader=False prevents Flask from watching Python stdlib files
    # (json/__init__.py, logging/__init__.py etc.) and restarting mid-request
    # which caused ERR_CONNECTION_RESET in the browser.
    # After changing backend code, just stop and restart the server manually.
    app.run(host=host, port=port, debug=debug, use_reloader=False)
