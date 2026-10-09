"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()
logger = logging.getLogger(__name__)

# Columns added after the first release. create_all() will not add a column to
# a table that already exists, so older databases need them patched in.
_ADDED_COLUMNS = [
    ("github_username",     "VARCHAR(255)"),
    ("github_access_token", "VARCHAR(500)"),
    ("github_repo",         "VARCHAR(255)"),
    ("github_branch",       "VARCHAR(255) DEFAULT 'main'"),
    ("github_folder",       "VARCHAR(255)"),
    ("password_hash",       "VARCHAR(255)"),
]


def _add_missing_columns(conn, existing_columns):
    """Add any column in _ADDED_COLUMNS that this database does not have yet."""
    from sqlalchemy import text

    for col_name, col_type in _ADDED_COLUMNS:
        if col_name not in existing_columns:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            logger.info(f"[Migration] Added missing column: users.{col_name}")


def _relax_google_id_not_null(conn, inspector):
    """
    Drop the NOT NULL constraint on users.google_id.

    Password-only accounts have no Google id, but the original schema declared
    the column NOT NULL. SQLite has no ALTER COLUMN, so the only way to relax a
    constraint is to rebuild the table and copy the rows across.

    Rebuilding from User.__table__ rather than hand-written DDL means the new
    table always matches the model, including any column added above.
    """
    from sqlalchemy import MetaData, text

    google_id = next(
        (c for c in inspector.get_columns('users') if c['name'] == 'google_id'),
        None,
    )
    if google_id is None or google_id.get('nullable', True):
        return  # Already nullable, or no such column: nothing to rebuild.

    from .user import User

    tmp_name = 'users_migration_tmp'
    tmp_meta = MetaData()
    tmp_table = User.__table__.to_metadata(tmp_meta, name=tmp_name)

    # Copy only the columns present in BOTH schemas. _add_missing_columns has
    # already run, so this is the model's columns minus anything the old
    # database has that the model has since dropped.
    existing = {c['name'] for c in inspector.get_columns('users')}
    shared = [c.name for c in User.__table__.columns if c.name in existing]
    collist = ", ".join(shared)

    conn.execute(text(f"DROP TABLE IF EXISTS {tmp_name}"))
    tmp_table.create(bind=conn)
    conn.execute(text(f"INSERT INTO {tmp_name} ({collist}) SELECT {collist} FROM users"))
    conn.execute(text("DROP TABLE users"))
    conn.execute(text(f"ALTER TABLE {tmp_name} RENAME TO users"))

    logger.info("[Migration] Rebuilt users table: google_id is now nullable")


def run_migrations(app):
    """
    Bring an existing database up to the current schema.

    Safe to run on every start: each step checks whether it is needed first.
    Failures are logged rather than raised so a schema quirk cannot stop the
    app from booting.
    """
    with app.app_context():
        try:
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            if 'users' not in inspector.get_table_names():
                return  # First run: create_all() builds it correctly.

            existing_columns = {col['name'] for col in inspector.get_columns('users')}

            with db.engine.connect() as conn:
                _add_missing_columns(conn, existing_columns)
                conn.commit()

            # Re-inspect: the rebuild copies whatever columns now exist.
            inspector = inspect(db.engine)
            with db.engine.connect() as conn:
                _relax_google_id_not_null(conn, inspector)
                conn.commit()

        except Exception as e:
            logger.warning(f"[Migration] Could not run migrations (non-fatal): {e}")


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)

    with app.app_context():
        # Run migrations first (patches any existing table), then create
        # anything that does not exist yet.
        run_migrations(app)
        db.create_all()
        logger.debug("Database initialized")
