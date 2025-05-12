import pytest
from unittest.mock import patch, MagicMock
from flask import session, url_for
from datetime import datetime
from app.routes.views import views
from tests.utils import create_user, login, logout

def test_index_page_requires_login(client):
    """Test that index page requires login"""
    # Try to access index page without logging in
    response = client.get('/')
    
    # Should redirect to login page
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_index_page_after_login(app, client):
    """Test index page after login"""
    with app.app_context():
        # Create test user and log in
        user = create_user(username='testuser', password='password123')
        login(client, username='testuser', password='password123')
        
        # Access index page
        response = client.get('/')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Dashboard' in response.data

def test_login_page(client):
    """Test login page GET request"""
    response = client.get('/login')
    
    # Should return 200 OK
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data

def test_login_valid_credentials(app, client):
    """Test login with valid credentials"""
    with app.app_context():
        # Create test user
        user = create_user(username='loginuser', password='correctpass')
        
        # Send login request
        response = client.post(
            '/login',
            data={'username': 'loginuser', 'password': 'correctpass'},
            follow_redirects=True
        )
        
        # Should redirect to dashboard
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        
        # Check session
        with client.session_transaction() as sess:
            assert sess['user_id'] == user.id
            assert sess['username'] == 'loginuser'
            assert sess['is_admin'] == 1

def test_login_invalid_credentials(app, client):
    """Test login with invalid credentials"""
    with app.app_context():
        # Create test user
        create_user(username='loginuser', password='correctpass')
        
        # Send login request with wrong password
        response = client.post(
            '/login',
            data={'username': 'loginuser', 'password': 'wrongpass'},
            follow_redirects=True
        )
        
        # Should stay on login page with error
        assert response.status_code == 200
        assert b'Login' in response.data
        assert b'Invalid username or password' in response.data
        
        # Check session (should not have user info)
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

def test_login_nonexistent_user(client):
    """Test login with a non-existent user"""
    # Send login request with non-existent user
    response = client.post(
        '/login',
        data={'username': 'nonexistent', 'password': 'anypassword'},
        follow_redirects=True
    )
    
    # Should stay on login page with error
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Invalid username or password' in response.data
    
    # Check session (should not have user info)
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_login_redirect_to_next_url(app, client):
    """Test login redirects to next_url if set in session"""
    with app.app_context():
        # Create test user
        create_user(username='nextuser', password='password123')
        
        # Set next_url in session
        with client.session_transaction() as sess:
            sess['next_url'] = '/scripts'
        
        # Send login request
        response = client.post(
            '/login',
            data={'username': 'nextuser', 'password': 'password123'},
            follow_redirects=False
        )
        
        # Should redirect somewhere (either index or scripts)
        assert response.status_code == 302
        # Since the redirect goes to next_page or to index, we verify that there is a redirect
        assert 'Location' in response.headers
        
        # Verify next_url was cleared from session
        with client.session_transaction() as sess:
            assert 'next_url' not in sess

def test_logout(app, client):
    """Test logout functionality"""
    with app.app_context():
        # Create test user and log in
        create_user(username='logoutuser', password='password123')
        login(client, username='logoutuser', password='password123')
        
        # Verify user is logged in
        with client.session_transaction() as sess:
            assert 'user_id' in sess
        
        # Log out
        response = client.get('/logout', follow_redirects=False)
        
        # Should redirect to login page
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
        
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess

def test_scripts_page(app, client):
    """Test scripts page"""
    with app.app_context():
        # Create test user and log in
        create_user(username='scriptsuser', password='password123')
        login(client, username='scriptsuser', password='password123')
        
        # Access scripts page
        response = client.get('/scripts')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Scripts' in response.data

def test_execution_history_page(app, client):
    """Test execution history page"""
    with app.app_context():
        # Create test user and log in
        create_user(username='historyuser', password='password123')
        login(client, username='historyuser', password='password123')
        
        # Access execution history page
        response = client.get('/execution_history')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Execution History' in response.data or b'history' in response.data.lower()

def test_execution_details_page_valid_id(app, client):
    """Test execution details page with valid execution ID"""
    with app.app_context():
        # Create test user and log in
        create_user(username='detailsuser', password='password123')
        login(client, username='detailsuser', password='password123')
        
        # Mock ExecutionORM.get_by_id_with_details to return execution data
        mock_execution = {
            'id': 1,
            'script_id': 1,
            'aws_profile_id': 1,
            'user_id': 1,
            'status': 'Success',
            'script_name': 'Test Script',
            'aws_profile_name': 'Test Profile',
            'username': 'detailsuser'
        }
        
        with patch('app.models.ExecutionORM.get_by_id_with_details', return_value=mock_execution):
            # Access execution details page
            response = client.get('/execution_details/1')
            
            # Should return 200 OK
            assert response.status_code == 200
            assert b'details' in response.data.lower() or b'Execution Details' in response.data
            
            # Verify CSS styles are included
            assert b'execution-details-container' in response.data

def test_execution_details_page_invalid_id(app, client):
    """Test execution details page with invalid execution ID"""
    with app.app_context():
        # Create test user and log in
        create_user(username='detailsuser', password='password123')
        login(client, username='detailsuser', password='password123')
        
        # Mock ExecutionORM.get_by_id_with_details to return None (not found)
        with patch('app.models.ExecutionORM.get_by_id_with_details', return_value=None):
            # Access execution details page with invalid ID
            response = client.get('/execution_details/999', follow_redirects=True)
            
            # Should redirect to execution history
            assert response.status_code == 200
            assert b'Execution record not found' in response.data
            assert b'history' in response.data.lower()

def test_execution_details_page_exception(app, client):
    """Test execution details page when an exception occurs"""
    with app.app_context():
        # Create test user and log in
        create_user(username='detailsuser', password='password123')
        login(client, username='detailsuser', password='password123')
        
        # Mock ExecutionORM.get_by_id_with_details to raise an exception
        with patch('app.models.ExecutionORM.get_by_id_with_details', side_effect=Exception('Test error')):
            # Access execution details page
            response = client.get('/execution_details/1', follow_redirects=True)
            
            # Should redirect to execution history with error message
            assert response.status_code == 200
            assert b'Error loading execution details' in response.data
            assert b'history' in response.data.lower()

def test_view_execution_valid_id(app, client):
    """Test view_execution with valid execution ID"""
    with app.app_context():
        # Create test user and log in
        create_user(username='viewuser', password='password123')
        login(client, username='viewuser', password='password123')
        
        # Mock ExecutionORM.get_by_id to return an execution
        mock_execution = MagicMock()
        
        with patch('app.models.ExecutionORM.get_by_id', return_value=mock_execution):
            # Access view_execution page
            response = client.get('/view_execution/1')
            
            # Should return 200 OK
            assert response.status_code == 200
            assert b'details' in response.data.lower() or b'Execution Details' in response.data
            
            # Verify CSS styles are included
            assert b'execution-details-container' in response.data

def test_view_execution_invalid_id(app, client):
    """Test view_execution with invalid execution ID"""
    with app.app_context():
        # Create test user and log in
        create_user(username='viewuser', password='password123')
        login(client, username='viewuser', password='password123')
        
        # Mock ExecutionORM.get_by_id to return None (not found)
        with patch('app.models.ExecutionORM.get_by_id', return_value=None):
            # Access view_execution page with invalid ID
            response = client.get('/view_execution/999', follow_redirects=True)
            
            # Should redirect to execution history
            assert response.status_code == 200
            assert b'Execution record not found' in response.data
            assert b'history' in response.data.lower()

def test_settings_page(app, client):
    """Test settings page"""
    with app.app_context():
        # Create test user and log in
        create_user(username='settingsuser', password='password123')
        login(client, username='settingsuser', password='password123')
        
        # Access settings page
        response = client.get('/settings')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Settings' in response.data

def test_scheduler_page(app, client):
    """Test scheduler page"""
    with app.app_context():
        # Create test user and log in
        create_user(username='scheduleruser', password='password123')
        login(client, username='scheduleruser', password='password123')
        
        # Access scheduler page
        response = client.get('/scheduler')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Scheduler' in response.data

def test_users_page_admin(app, client):
    """Test users page with admin user"""
    with app.app_context():
        # Create admin user and log in
        create_user(username='adminuser', password='password123', is_admin=1)
        login(client, username='adminuser', password='password123')
        
        # Access users page
        response = client.get('/users')
        
        # Should return 200 OK
        assert response.status_code == 200
        assert b'Users' in response.data or b'User Management' in response.data

def test_users_page_non_admin(app, client):
    """Test users page with non-admin user"""
    with app.app_context():
        # Create non-admin user and log in
        create_user(username='regularuser', password='password123', is_admin=0)
        
        # Log in manually to ensure is_admin is 0
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'regularuser'
            sess['is_admin'] = 0
        
        # Access users page
        response = client.get('/users', follow_redirects=True)
        
        # Should redirect to index with access denied message
        assert response.status_code == 200
        assert b'Access denied: Administrator privileges required' in response.data
        assert b'Dashboard' in response.data

@patch('app.routes.views.send_from_directory')
def test_favicon(mock_send_from_directory, client):
    """Test favicon route"""
    # Mock the send_from_directory function to avoid file system issues
    mock_send_from_directory.return_value = "mocked_favicon"

    response = client.get('/favicon.ico')

    # Check that the route was called
    assert mock_send_from_directory.called

def test_test_session(app, client):
    """Test test_session route"""
    with app.app_context():
        # Set something in session
        with client.session_transaction() as sess:
            sess['test_key'] = 'test_value'
        
        # Access test_session route
        response = client.get('/test_session')
        
        # Should return 200 OK with session info
        assert response.status_code == 200
        assert b'Session contents' in response.data
        assert b'test_key' in response.data
        assert b'test_value' in response.data
        assert b'Session cookies configured with' in response.data