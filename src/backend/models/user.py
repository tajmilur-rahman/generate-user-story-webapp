"""
User model for authentication
"""
from flask_login import UserMixin
from .database import db

class User(UserMixin, db.Model):
    """User model for Google OAuth authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
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
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'github_username': self.github_username,
            'github_owner': self.github_owner,
            'github_repo': self.github_repo,
            'github_branch': self.github_branch,
            'github_folder': self.github_folder
        }
