from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import os


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure the 'instance' folder exists for our SQLite DB
    instance_path = os.path.join(app.instance_path)
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Instance folder created at: {instance_path}")
    
    # Initialize our extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # --- Register Blueprints ---
    # We will register our routes (which we'll put in a Blueprint)
    # here to keep our app modular.
    
    # We import here to avoid circular imports
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # We will also import our database models here
    # so that Flask-Migrate can "see" them.
    from app import models

    return app