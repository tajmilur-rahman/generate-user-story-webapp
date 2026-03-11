"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()
logger = logging.getLogger(__name__)

def run_migrations(app):
    """
    Run lightweight schema migrations to add new columns to existing tables.
    This handles the case where an older database exists without newer columns.
    SQLAlchemy's create_all() won't add columns to existing tables, so we do it manually.
    """
    with app.app_context():
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            # Check if users table exists first
            if 'users' not in inspector.get_table_names():
                return  # Table doesn't exist yet, create_all() will handle it
            
            # Get existing columns in the users table
            existing_columns = {col['name'] for col in inspector.get_columns('users')}
            
            # Define new columns that may be missing in older databases
            new_columns = [
                ("github_username",     "VARCHAR(255)"),
                ("github_access_token", "VARCHAR(500)"),
                ("github_repo",         "VARCHAR(255)"),
                ("github_branch",       "VARCHAR(255) DEFAULT 'main'"),
                ("github_folder",       "VARCHAR(255)"),
            ]
            
            with db.engine.connect() as conn:
                for col_name, col_type in new_columns:
                    if col_name not in existing_columns:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"[Migration] Added missing column: users.{col_name}")
                        print(f"[Migration] Added column: users.{col_name}")
                conn.commit()
                
        except Exception as e:
            logger.warning(f"[Migration] Could not run migrations (non-fatal): {e}")

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Run migrations first (adds any missing columns to existing tables)
        run_migrations(app)
        # Then create any completely new tables
        db.create_all()
        print("[OK] Database initialized")

