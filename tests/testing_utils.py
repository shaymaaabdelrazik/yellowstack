import os
import sys
from flask import Flask

# Import the utility module from the application
from app.utils.db import db, init_db_sqlalchemy
from app.routes import all_blueprints

def create_test_app(test_config=None):
    """
    Create a Flask application for testing.
    This version skips service initialization.
    
    Args:
        test_config: Configuration to use for testing
    
    Returns:
        Flask: The configured Flask application for testing
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True,
                static_folder='../static', template_folder='../templates')
    
    # Load default configuration
    app.config.from_object('app.config.TestingConfig')
    
    # Override with test config if provided
    if test_config:
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Initialize database with SQLAlchemy
    init_db_sqlalchemy(app)
    
    # Register all blueprints for API testing
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
    
    # Initialize CSRF protection if enabled in configuration
    if app.config.get('WTF_CSRF_ENABLED', False):
        from flask_wtf.csrf import CSRFProtect
        csrf = CSRFProtect()
        csrf.init_app(app)
    
    return app

def setup_test_db(app):
    """
    Set up the test database for this test context
    
    Args:
        app: Flask application
    """
    with app.app_context():
        # Create all tables
        db.create_all()

def teardown_test_db(app):
    """
    Tear down the test database after tests
    
    Args:
        app: Flask application
    """
    with app.app_context():
        db.session.remove()
        db.drop_all()