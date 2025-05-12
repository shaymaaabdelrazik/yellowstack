"""
Configuration file for CSRF protection tests
"""
import os
import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_wtf.csrf import CSRFProtect

# Import the application creation function for tests
from tests.testing_utils import create_test_app

@pytest.fixture
def csrf_app():
    """
    Creates a Flask application with CSRF protection enabled for testing
    """
    # Create a test application with CSRF protection activated
    app = create_test_app({
        'TESTING': True,
        'SECRET_KEY': 'test_key_for_csrf_test',
        'DATABASE': ':memory:',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'PRESERVE_CONTEXT_ON_EXCEPTION': False,
        # Enable CSRF protection for tests (disabled by default in testing_utils.py)
        'WTF_CSRF_ENABLED': True,
        'WTF_CSRF_SECRET_KEY': 'csrf_test_key'
    })
    
    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Create application context
    with app.app_context():
        # Create tables in the database
        from app.models.user_orm import UserORM
        from app.utils.db import db
        db.create_all()
        
        # Create test admin user for testing
        # Check if user exists already to avoid integrity errors
        existing_admin = UserORM.get_by_username('csrf_admin')
        if not existing_admin:
            admin = UserORM(username='csrf_admin', is_admin=True)
            admin.set_password('password')
            db.session.add(admin)
            db.session.commit()
        
        yield app
        
        # Clean up after tests
        db.session.remove()
        db.drop_all()

@pytest.fixture
def csrf_client(csrf_app):
    """
    Creates a test client with CSRF protection enabled
    """
    with csrf_app.test_client() as client:
        # Save an empty session context for client.session_transaction()
        with client.session_transaction() as session:
            pass
        yield client

@pytest.fixture
def csrf_auth_client(csrf_client):
    """
    Creates an authenticated test client with CSRF protection enabled
    """
    with csrf_client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'admin'
        session['is_admin'] = True
    return csrf_client