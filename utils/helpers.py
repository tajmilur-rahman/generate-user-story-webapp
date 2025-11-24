import os

ALLOWED_EXTENSIONS = {'docx', 'doc', 'txt', 'md'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
