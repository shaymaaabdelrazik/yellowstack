import os
import sys
import pytest
from flask import Flask
from flask.testing import FlaskClient
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Add parent directory to path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.db import db
from tests.testing_utils import create_test_app

# Suppress InsecureRequestWarning globally for all tests
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

class TestClient(FlaskClient):
    """Custom test client with session management"""
    def open(self, *args, **kwargs):
        # When testing JSON APIs, set the content type automatically
        if 'json' in kwargs:
            kwargs.setdefault('content_type', 'application/json')
        return super().open(*args, **kwargs)

@pytest.fixture
def app():
    """Create a Flask application for testing"""
    # Create a test app without initializing services
    app = create_test_app({
        'TESTING': True,
        'SECRET_KEY': 'test_key',
        'DATABASE': ':memory:',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'PRESERVE_CONTEXT_ON_EXCEPTION': False,
        # We leave CSRF protection disabled for non-CSRF specific tests
        'WTF_CSRF_ENABLED': False
    })
    
    # Set test client
    app.test_client_class = TestClient
    
    # Register a Jinja2 function for csrf_token which returns a valid token
    # in tests without having to enable CSRF protection
    @app.context_processor
    def csrf_token_processor():
        def csrf_token():
            return "test_csrf_token_for_jinja_templates"
        return dict(csrf_token=csrf_token)
    
    # Create an application context
    with app.app_context():
        # Create database tables, including scheduler tables
        from app.models.scheduler_orm import ScheduleORM
        db.create_all()
        yield app
        
        # Clean up after test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a CLI test runner for the app"""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """Create an authenticated test client"""
    with client.session_transaction() as session:
        session['logged_in'] = True
        session['user_id'] = 1
        session['username'] = 'testuser'
        session['is_admin'] = True
    return client