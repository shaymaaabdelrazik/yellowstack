import pytest
from unittest.mock import patch, MagicMock
from flask import session, url_for, Flask, Blueprint, request
from app.auth.login_required import login_required, admin_required
from tests.utils import create_user, login, logout

def test_login_required_decorator_user_not_logged_in(app, client):
    """Test login_required decorator when user is not logged in"""
    with app.app_context():
        # Create a test blueprint with a protected route
        bp = Blueprint('test_bp', __name__)
        
        @bp.route('/protected')
        @login_required
        def protected_route():
            return 'Protected Content'
        
        # Register the blueprint
        app.register_blueprint(bp)
        
        # Try to access the protected route without logging in
        response = client.get('/protected')
        
        # Should redirect to login page
        assert response.status_code == 302
        assert '/login' in response.location
        
        # Check if the next_url was set in session
        with client.session_transaction() as sess:
            assert sess.get('next_url') == '/protected'

def test_login_required_decorator_invalid_user(app, client):
    """Test login_required decorator with a user ID that no longer exists"""
    with app.app_context():
        # Create a test blueprint with a protected route
        bp = Blueprint('test_bp', __name__)
        
        @bp.route('/protected')
        @login_required
        def protected_route():
            return 'Protected Content'
        
        # Register the blueprint
        app.register_blueprint(bp)
        
        # Add non-existent user_id to session
        with client.session_transaction() as sess:
            sess['user_id'] = 9999  # ID that doesn't exist
        
        # Patch UserORM.get_by_id
        with patch('app.models.UserORM.get_by_id') as mock_get_by_id:
            # Mock UserORM.get_by_id to return None (user not found)
            mock_get_by_id.return_value = None
            # Try to access the protected route
            response = client.get('/protected')
            
            # Should redirect to login
            assert response.status_code == 302
            assert '/login' in response.location
            
            # Check if session was cleared
            with client.session_transaction() as sess:
                assert 'user_id' not in sess

def test_login_required_decorator_valid_user(app, client):
    """Test login_required decorator with a valid logged-in user"""
    with app.app_context():
        # Create a test blueprint with a protected route
        bp = Blueprint('test_bp', __name__)

        @bp.route('/protected')
        @login_required
        def protected_route():
            return 'Protected Content'

        # Register the blueprint
        app.register_blueprint(bp)

        # Create and log in a user
        user = create_user(username='protected_user', password='password123')
        login(client, username='protected_user', password='password123')

        # Patch UserORM.get_by_id
        with patch('app.models.UserORM.get_by_id') as mock_get_by_id:
            # Mock UserORM.get_by_id to return valid user
            mock_get_by_id.return_value = user

            # Access the protected route
            response = client.get('/protected')

            # Should return 200 OK with the content
            assert response.status_code == 200
            assert b'Protected Content' in response.data

def test_admin_required_non_admin_user(app, client):
    """Test admin_required decorator with a non-admin user"""
    with app.app_context():
        # Create a test blueprint with an admin-only route
        bp = Blueprint('test_bp', __name__)
        
        @bp.route('/admin-only')
        @admin_required
        def admin_only_route():
            return 'Admin Only Content'
        
        # Register the blueprint
        app.register_blueprint(bp)
        
        # Create and log in a non-admin user
        user = create_user(username='non_admin_user', password='password123', is_admin=0)
        
        # Set session manually to ensure is_admin is 0
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = 0
        
        # Try to access the admin-only route
        response = client.get('/admin-only')
        
        # Should redirect to index with access denied
        assert response.status_code == 302
        assert '/index' in response.location or '/' in response.location

def test_admin_required_admin_user(app, client):
    """Test admin_required decorator with an admin user"""
    with app.app_context():
        # Create a test blueprint with an admin-only route
        bp = Blueprint('test_bp', __name__)
        
        @bp.route('/admin-only')
        @admin_required
        def admin_only_route():
            return 'Admin Only Content'
        
        # Register the blueprint
        app.register_blueprint(bp)
        
        # Create and log in an admin user
        user = create_user(username='admin_user', password='password123', is_admin=1)
        
        # Set session manually to ensure is_admin is 1
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = 1
        
        # Access the admin-only route
        response = client.get('/admin-only')
        
        # Should return 200 OK with the content
        assert response.status_code == 200
        assert b'Admin Only Content' in response.data

def test_admin_required_no_session(app, client):
    """Test admin_required decorator with no session (not logged in)"""
    with app.app_context():
        # Create a test blueprint with an admin-only route
        bp = Blueprint('test_bp', __name__)
        
        @bp.route('/admin-only')
        @admin_required
        def admin_only_route():
            return 'Admin Only Content'
        
        # Register the blueprint
        app.register_blueprint(bp)
        
        # Clear session
        with client.session_transaction() as sess:
            sess.clear()
        
        # Try to access the admin-only route without any session
        response = client.get('/admin-only')
        
        # Should redirect to index with access denied
        assert response.status_code == 302
        assert '/index' in response.location or '/' in response.location