import os
from dotenv import load_dotenv

# Find the base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

# Load the .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = 'run.py'
    FLASK_ENV = 'development' # Change to 'production' on Render

    # Database
    # This URI is for our local SQLite database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
    
    # This is a setting for SQLAlchemy that we'll just set to False
    # to disable a feature we don't need, which saves resources.
    SQLALCHEMY_TRACK_MODIFICATIONS = False