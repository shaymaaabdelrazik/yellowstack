import pytest
from unittest.mock import patch, MagicMock
from flask import session, url_for
from app.services.auth_service import auth_service
from app.auth.login_required import login_required, admin_required
from tests.utils import create_user, login, logout

def test_login(app, client):
    """Test login functionality"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testlogin', password='password123')
        
        # Make login request
        response = login(client, username='testlogin', password='password123')
        
        # Check response
        assert response.status_code == 200
        
        # Check session
        with client.session_transaction() as sess:
            assert sess['user_id'] == user.id
            assert sess['username'] == 'testlogin'
            assert sess['is_admin'] == 1  # Default is admin in create_user

def test_login_invalid_credentials(app, client):
    """Test login with invalid credentials"""
    with app.app_context():
        # Create a test user
        create_user(username='testlogin', password='password123')
        
        # Make login request with wrong password
        response = login(client, username='testlogin', password='wrongpassword')
        
        # Check response
        assert response.status_code == 200  # Login page with error
        
        # Ensure we're still on the login page (not redirected to dashboard)
        assert b'Login' in response.data
        assert b'Invalid username or password' in response.data
        
        # Check session (should not have user info)
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

def test_login_nonexistent_user(app, client):
    """Test login with nonexistent user"""
    with app.app_context():
        # Make login request with nonexistent user
        response = login(client, username='nonexistent', password='password123')
        
        # Check response
        assert response.status_code == 200  # Login page with error
        
        # Ensure we're still on the login page
        assert b'Login' in response.data
        assert b'Invalid username or password' in response.data
        
        # Check session (should not have user info)
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

def test_logout(app, client):
    """Test logout functionality"""
    with app.app_context():
        # Create a test user and log in
        create_user(username='testlogout', password='password123')
        login(client, username='testlogout', password='password123')
        
        # Check session before logout
        with client.session_transaction() as sess:
            assert 'user_id' in sess
        
        # Perform logout
        response = logout(client)
        
        # Check response
        assert response.status_code == 200
        
        # Check session after logout
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

def test_login_required_decorator(app, client):
    """Test login_required decorator"""
    # For simplicity, we'll test this by checking an existing protected route
    # rather than creating a new one, as that would require mocking User.get_by_id
    
    with app.app_context():
        # Try to access a protected route (scripts page) without login
        response = client.get('/scripts')
        
        # Should redirect to login
        assert response.status_code in [302, 401]  # Either redirect or unauthorized
        if response.status_code == 302:
            assert '/login' in response.location
        
        # Login
        user = create_user(username='protecteduser', password='password123')
        login(client, username='protecteduser', password='password123')
        
        # Try accessing scripts page after login
        response = client.get('/scripts')
        
        # Should succeed or redirect to a dashboard page
        assert response.status_code in [200, 302]

def test_admin_required_decorator(app, client):
    """Test admin_required decorator"""
    # For simplicity, we'll check access to an admin page (users)
    with app.app_context():
        # Create a regular (non-admin) user
        regular_user = create_user(username='regularuser', password='password123', is_admin=0)
        
        # Log in as regular user
        with client.session_transaction() as sess:
            sess['user_id'] = regular_user.id
            sess['username'] = regular_user.username
            sess['is_admin'] = 0
        
        # Try to access a route requiring admin privileges (users page)
        response = client.get('/users')
        
        # Should redirect to index with access denied or return 403 unauthorized
        assert response.status_code in [302, 403]
        
        # Create admin user and login
        admin_user = create_user(username='adminuser', password='password123', is_admin=1)
        
        # Log in as admin user
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['username'] = admin_user.username
            sess['is_admin'] = 1
        
        # Try accessing the admin page
        response = client.get('/users')
        
        # Should succeed or redirect to dashboard
        assert response.status_code in [200, 302]

def test_get_current_user(app, client):
    """Test get_current_user method"""
    with app.app_context():
        # Create a test user
        user = create_user(username='currentuser', password='password123')
        
        # Login to set up session
        login(client, username='currentuser', password='password123')
        
        # Make a request to set up request context
        with app.test_request_context():
            # Manually set session to match the client session
            with client.session_transaction() as sess:
                session_data = dict(sess)
            
            for key, value in session_data.items():
                session[key] = value
            
            # Get current user
            current_user = auth_service.get_current_user()
            
            # Check user is returned correctly
            assert current_user is not None
            assert current_user.id == user.id
            assert current_user.username == 'currentuser'

def test_get_current_user_not_logged_in(app, client):
    """Test get_current_user when not logged in"""
    with app.app_context():
        # Make a request to set up request context
        with app.test_request_context():
            # Ensure session is clear
            session.clear()
            
            # Get current user
            current_user = auth_service.get_current_user()
            
            # Check no user is returned
            assert current_user is None

def test_change_password(app, client):
    """Test change_password functionality"""
    with app.app_context():
        # Create a test user
        user = create_user(username='passworduser', password='oldpassword')
        
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = user.is_admin
        
        # Change password
        result, message = auth_service.change_password(user.id, 'oldpassword', 'newpassword')
        
        # Check result
        assert result is True
        assert message is None
        
        # Verify new password works for login
        logout(client)
        response = login(client, username='passworduser', password='newpassword')
        
        # Should redirect to dashboard on success
        assert response.status_code == 200
        
        # Check session after login with new password
        with client.session_transaction() as sess:
            assert sess['user_id'] == user.id

def test_change_password_incorrect_current(app, client):
    """Test change_password with incorrect current password"""
    with app.app_context():
        # Create a test user
        user = create_user(username='passworduser2', password='correctpassword')
        
        # Attempt to change password with wrong current password
        result, message = auth_service.change_password(user.id, 'wrongpassword', 'newpassword')
        
        # Check result
        assert result is False
        assert 'incorrect' in message.lower()

def test_admin_update_password(app, auth_client):
    """Test admin_update_password functionality"""
    with app.app_context():
        # Create a test user
        user = create_user(username='adminresetuser', password='oldpassword', is_admin=0)
        
        # Admin updates password
        with patch.object(auth_service, 'admin_update_password', wraps=auth_service.admin_update_password) as mock_update:
            result, message = auth_service.admin_update_password(user.id, 'adminsetpassword')
            
            # Check result
            assert result is True
            assert message is None
            
            # Verify function was called with correct arguments
            mock_update.assert_called_once_with(user.id, 'adminsetpassword')
        
        # Verify new password works for login
        response = login(auth_client, username='adminresetuser', password='adminsetpassword')
        
        # Should redirect to dashboard on success
        assert response.status_code == 200
        
        # Check session after login with new password
        with auth_client.session_transaction() as sess:
            assert sess['user_id'] is not None

def test_create_user(app, auth_client):
    """Test create_user functionality"""
    with app.app_context():
        # Mock the create_user method to isolate test
        with patch.object(auth_service, 'create_user', wraps=auth_service.create_user) as mock_create:
            # Call create_user
            result, user_id = auth_service.create_user('newuser', 'newpassword', 1)
            
            # Check result
            assert result is True
            assert user_id is not None
            
            # Verify function was called with correct arguments
            mock_create.assert_called_once_with('newuser', 'newpassword', 1)
            
            # Check user exists in database
            user = auth_service.user_adapter.get_by_username('newuser')
            assert user is not None
            assert user.username == 'newuser'
            assert user.is_admin == 1

def test_create_user_duplicate(app, auth_client):
    """Test create_user with duplicate username"""
    with app.app_context():
        # Create a user first
        create_user(username='duplicateuser', password='password123')
        
        # Attempt to create user with same username
        result, message = auth_service.create_user('duplicateuser', 'newpassword', 0)
        
        # Check result
        assert result is False
        assert 'already exists' in message.lower()

def test_delete_user(app, auth_client):
    """Test delete_user functionality"""
    with app.app_context():
        # Create a user that we will delete
        user = create_user(username='userdelete', password='password123', is_admin=0)
        
        # Fake admin_id different from user.id
        admin_id = 999
        assert user.id != admin_id  # To avoid deleting self

        with patch.object(auth_service.user_adapter, 'delete') as mock_delete, \
             patch.object(auth_service.user_adapter, 'get_by_id') as mock_get_by_id:
            mock_delete.return_value = True
            mock_get_by_id.return_value = user
            
            # Remove user
            result, message = auth_service.delete_user(user.id, admin_id)
            
            assert result is True
            assert message is None
            mock_delete.assert_called_once_with(user.id)


def test_delete_user_self(app, auth_client):
    """Test delete_user attempting to delete self"""
    with app.app_context():
        # Admin user ID (from auth_client fixture)
        admin_user_id = 1
        
        # Attempt to delete self
        result, message = auth_service.delete_user(admin_user_id, admin_user_id)
        
        # Check result (should fail)
        assert result is False
        assert 'cannot delete your own account' in message.lower()

def test_toggle_admin(app, auth_client):
    """Test toggle_admin functionality"""
    with app.app_context():
        # Create a regular user
        user = create_user(username='toggleuser', password='password123', is_admin=0)
        
        # We need to patch both toggle_admin to avoid test dependency
        # and toggle the adapter.toggle_admin method
        with patch.object(auth_service, 'toggle_admin', wraps=auth_service.toggle_admin) as mock_toggle, \
             patch.object(auth_service.user_adapter, 'toggle_admin') as mock_adapter_toggle:
             
            # Configure adapter mock to return True
            mock_adapter_toggle.return_value = True
            
            # Toggle user to admin
            result, message = auth_service.toggle_admin(user.id, 1)  # Current user ID 1 from auth_client
            
            # Check result
            assert result is True
            assert message is None
            
            # Verify function was called correctly
            mock_toggle.assert_called_once_with(user.id, 1)
            
            # Verify adapter was called with admin=1
            mock_adapter_toggle.assert_called_once_with(user.id, 1)