"""
User model for authentication
"""
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db


class User(UserMixin, db.Model):
    """
    A user account.

    An account can authenticate by password, by Google, or by both. Email is
    the identity that joins the two: signing in with Google for an address that
    already has a password lands on the same row rather than creating a second
    account.

    Exactly one of google_id and password_hash may be null, so neither can be
    declared NOT NULL at the column level.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    # Null for accounts that have only ever signed in with a password.
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # Null for accounts that have only ever signed in with Google. Stores a
    # Werkzeug hash (scrypt by default), never the password itself.
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(255))
    picture = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    # GitHub integration fields (optional)
    github_username = db.Column(db.String(255), nullable=True)
    github_access_token = db.Column(db.String(500), nullable=True)
    github_owner = db.Column(db.String(255), nullable=True)  # Owner (user or organization)
    github_repo = db.Column(db.String(255), nullable=True)
    github_branch = db.Column(db.String(255), nullable=True, default='main')
    github_folder = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        """Hash and store a password. Rejects an empty one outright."""
        if not password:
            raise ValueError("Password must not be empty")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify a password against the stored hash.

        Returns False for a Google-only account rather than raising, so the
        caller can treat "wrong password" and "no password set" identically and
        avoid disclosing which accounts exist.
        """
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def has_password(self):
        return bool(self.password_hash)

    def to_dict(self):
        """Convert user to dictionary. Never includes the password hash."""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'has_password': self.has_password,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'github_username': self.github_username,
            'github_owner': self.github_owner,
            'github_repo': self.github_repo,
            'github_branch': self.github_branch,
            'github_folder': self.github_folder
        }
