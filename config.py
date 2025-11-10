import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = 'run.py'

    # --- SMART DATABASE CONFIG ---
    
    # Get the DATABASE_URL from the environment (this is for Render)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        # Render's free PostgreSQL URLs start with 'postgres://'
        # but SQLAlchemy 1.4+ needs 'postgresql://'
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    # Use Render's DB if available, otherwise fall back to local SQLite
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')

    # This is a setting for SQLAlchemy that we'll just set to False
    # to disable a feature we don't need, which saves resources.
    SQLALCHEMY_TRACK_MODIFICATIONS = False