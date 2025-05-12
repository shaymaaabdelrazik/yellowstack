from flask import current_app
from flask_sqlalchemy import SQLAlchemy
import logging
import os

# Get the existing logger from the application
logger = logging.getLogger('yellowstack')

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db_sqlalchemy(app):
    """
    Initialize the SQLAlchemy database connection.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing SQLAlchemy database connection")
    
    # Set up SQLAlchemy config
    db_path = app.config['DATABASE']
    
    # If it's not an in-memory database, check if the file exists
    if db_path != ':memory:' and not os.path.exists(db_path):
        logger.warning(f"Database file {db_path} does not exist. Creating new database.")
        # Make sure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    # Test the connection and create tables if they don't exist
    try:
        with app.app_context():
            db.engine.connect()
            # Create all tables
            db.create_all()
            logger.info(f"Successfully connected to database with SQLAlchemy: {db_path}")
            
            # Create default admin user if not exists
            create_default_admin_user()
            
            # Create default settings
            create_default_settings()
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy database: {str(e)}")
        raise

def create_default_admin_user():
    """Create default admin user if it doesn't already exist"""
    from app.models.user_orm import UserORM
    
    try:
        # Check if admin user exists
        admin = UserORM.get_by_username('admin')
        if admin is None:
            logger.info("Creating default admin user")
            admin = UserORM(
                username='admin',
                password='admin',  # Will be hashed in UserORM constructor
                is_admin=1
            )
            admin.save()
            logger.info("Default admin user created successfully")
        else:
            logger.info("Admin user already exists, skipping creation")
    except Exception as e:
        logger.error(f"Error creating default admin user: {str(e)}")
        # Continue execution even if admin creation fails

def create_default_settings():
    """Create default application settings if they don't exist"""
    from app.models.setting_orm import SettingORM
    
    default_settings = {
        "history_limit": "10",
        "enable_ai_help": "true",
        "app_version": "1.0.0",
        "timezone": "UTC"
    }
    
    try:
        for key, value in default_settings.items():
            # Check if setting exists
            setting = SettingORM.get_by_key(key)
            if setting is None:
                # Create setting
                setting = SettingORM(key=key, value=value)
                setting.save()
        logger.info("Default settings created or verified")
    except Exception as e:
        logger.error(f"Error creating default settings: {str(e)}")
        # Continue execution even if settings creation fails