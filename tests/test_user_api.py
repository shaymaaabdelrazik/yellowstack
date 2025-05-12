import pytest
import json
from unittest.mock import patch, MagicMock
from flask import session
from app.models.user_orm import UserORM
from app.services.auth_service import auth_service
from tests.utils import create_user

def test_get_users(app, auth_client):
    """Test get_users endpoint (admin only)"""
    with app.app_context():
        # Create some test users
        user1 = create_user(username='user1', is_admin=0)
        user2 = create_user(username='user2', is_admin=0)
        
        # Make request to get all users
        response = auth_client.get('/api/users')
        
        # Check response
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert len(data['users']) >= 2
        
        # Check if test users are in the response
        usernames = [user.get('username') for user in data['users']]
        assert 'user1' in usernames
        assert 'user2' in usernames

def test_get_users_unauthorized(app, client):
    """Test get_users endpoint without admin privileges"""
    with app.app_context():
        # Set session for non-admin user
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 1
            sess['username'] = 'regular_user'
            sess['is_admin'] = 0
        
        # Make request to get all users
        response = client.get('/api/users')
        
        # Check response
        assert response.status_code == 403
        data = response.json
        assert data['success'] is False
        assert 'Unauthorized' in data['message']

def test_add_user(app, auth_client):
    """Test add_user endpoint (admin only)"""
    with app.app_context():
        # Prepare data for new user
        user_data = {
            'username': 'newuser',
            'password': 'newpassword',
            'is_admin': False
        }
        
        # Mock the create_user method to avoid actually creating a user
        with patch.object(auth_service, 'create_user') as mock_create_user:
            # Configure mock to return success
            mock_create_user.return_value = (True, 123)  # (success, user_id)
            
            # Make request to add user
            response = auth_client.post('/api/users', json=user_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['user_id'] == 123
            
            # Verify create_user was called with correct arguments
            mock_create_user.assert_called_once_with(
                'newuser', 'newpassword', 0
            )

def test_add_user_missing_data(app, auth_client):
    """Test add_user endpoint with missing data"""
    with app.app_context():
        # Prepare incomplete data
        incomplete_data = {
            'username': 'newuser'
            # Missing password
        }
        
        # Make request with incomplete data
        response = auth_client.post('/api/users', json=incomplete_data)
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_add_user_duplicate(app, auth_client):
    """Test add_user endpoint with duplicate username"""
    with app.app_context():
        # Prepare data for new user
        user_data = {
            'username': 'duplicate_user',
            'password': 'password123',
            'is_admin': False
        }
        
        # Mock the create_user method to simulate duplicate username
        with patch.object(auth_service, 'create_user') as mock_create_user:
            # Configure mock to return failure
            mock_create_user.return_value = (False, "A user with this username already exists")
            
            # Make request to add user
            response = auth_client.post('/api/users', json=user_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'already exists' in data['message']

def test_get_user_profile(app, client):
    """Test get_user_profile endpoint"""
    with app.app_context():
        # Create a test user
        user = create_user(username='profile_user')
        
        # Set up session
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = user.is_admin
        
        # Mock the get_current_user method
        with patch.object(auth_service, 'get_current_user') as mock_get_user:
            # Configure mock to return the user
            mock_get_user.return_value = user
            
            # Make request to get user profile
            response = client.get('/api/users/profile')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['user']['username'] == 'profile_user'

def test_get_user_profile_not_found(app, client):
    """Test get_user_profile when user is not found"""
    with app.app_context():
        # Set up session
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 999  # Non-existent user ID
            sess['username'] = 'ghost_user'
            sess['is_admin'] = 0
        
        # Mock the get_current_user method
        with patch.object(auth_service, 'get_current_user') as mock_get_user:
            # Configure mock to return None (user not found)
            mock_get_user.return_value = None
            
            # Make request to get user profile
            response = client.get('/api/users/profile')
            
            # Check response
            assert response.status_code == 404
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_delete_user(app, auth_client):
    """Test delete_user endpoint (admin only)"""
    with app.app_context():
        # Create a test user to delete
        user = create_user(username='user_to_delete')
        
        # Mock the delete_user method
        with patch.object(auth_service, 'delete_user') as mock_delete_user, \
             patch.object(auth_service.user_adapter, 'get_by_id') as mock_get_by_id:
            # Configure mocks
            mock_delete_user.return_value = (True, None)
            
            # Mock user retrieval for logging
            mock_user = MagicMock()
            mock_user.username = 'user_to_delete'
            mock_get_by_id.return_value = mock_user
            
            # Make request to delete user
            response = auth_client.delete(f'/api/users/{user.id}')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'deleted successfully' in data['message'].lower()
            
            # Verify delete_user was called with correct arguments
            mock_delete_user.assert_called_once_with(user.id, 1)  # user_id, current_user_id

def test_delete_user_self(app, auth_client):
    """Test delete_user endpoint trying to delete self (should fail)"""
    with app.app_context():
        # Set admin user ID (from auth_client fixture)
        user_id = 1
        
        # Mock the delete_user method
        with patch.object(auth_service, 'delete_user') as mock_delete_user:
            # Configure mock to return failure (cannot delete self)
            mock_delete_user.return_value = (
                False, "You cannot delete your own account"
            )
            
            # Make request to delete self
            response = auth_client.delete(f'/api/users/{user_id}')
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'cannot delete your own account' in data['message'].lower()

def test_toggle_admin(app, auth_client):
    """Test toggle_admin endpoint (admin only)"""
    with app.app_context():
        # Create a test user
        user = create_user(username='regular_user', is_admin=0)
        
        # Prepare request data
        data = {'is_admin': True}
        
        # Mock the toggle_admin method
        with patch.object(auth_service, 'toggle_admin') as mock_toggle_admin, \
             patch.object(auth_service.user_adapter, 'get_by_id') as mock_get_by_id:
            # Configure mocks
            mock_toggle_admin.return_value = (True, None)
            
            # Mock user retrieval for logging
            mock_user = MagicMock()
            mock_user.username = 'regular_user'
            mock_get_by_id.return_value = mock_user
            
            # Make request to toggle admin status
            response = auth_client.post(f'/api/users/{user.id}/admin', json=data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'granted' in data['message'].lower()
            
            # Verify toggle_admin was called with correct arguments
            mock_toggle_admin.assert_called_once_with(user.id, 1)

def test_toggle_admin_missing_data(app, auth_client):
    """Test toggle_admin endpoint with missing data"""
    with app.app_context():
        # Create a test user
        user = create_user(username='regular_user', is_admin=0)
        
        # Make request without data
        response = auth_client.post(f'/api/users/{user.id}/admin', json={})
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_change_password(app, client):
    """Test change_password endpoint"""
    with app.app_context():
        # Create a test user
        user = create_user(username='password_user', password='oldpassword')
        
        # Set up session
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = 0
        
        # Prepare request data
        data = {
            'current_password': 'oldpassword',
            'new_password': 'newpassword'
        }
        
        # Mock the change_password method
        with patch.object(auth_service, 'change_password') as mock_change_password:
            # Configure mock to return success
            mock_change_password.return_value = (True, None)
            
            # Make request to change password
            response = client.post('/api/users/change_password', json=data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'changed successfully' in data['message'].lower()
            
            # Verify change_password was called with correct arguments
            mock_change_password.assert_called_once_with(
                user.id, 'oldpassword', 'newpassword'
            )

def test_change_password_incorrect(app, client):
    """Test change_password with incorrect current password"""
    with app.app_context():
        # Create a test user
        user = create_user(username='password_user', password='oldpassword')
        
        # Set up session
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['is_admin'] = 0
        
        # Prepare request data with wrong current password
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword'
        }
        
        # Mock the change_password method
        with patch.object(auth_service, 'change_password') as mock_change_password:
            # Configure mock to return failure
            mock_change_password.return_value = (
                False, "Current password is incorrect"
            )
            
            # Make request to change password
            response = client.post('/api/users/change_password', json=data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'incorrect' in data['message'].lower()

def test_update_user_password(app, auth_client):
    """Test update_user_password endpoint (admin only)"""
    with app.app_context():
        # Create a test user
        user = create_user(username='password_update_user')
        
        # Prepare request data
        data = {'new_password': 'adminsetpassword'}
        
        # Mock the admin_update_password method
        with patch.object(auth_service, 'admin_update_password') as mock_update_password, \
             patch.object(auth_service.user_adapter, 'get_by_id') as mock_get_by_id:
            # Configure mocks
            mock_update_password.return_value = (True, None)
            
            # Mock user retrieval for logging
            mock_user = MagicMock()
            mock_user.username = 'password_update_user'
            mock_get_by_id.return_value = mock_user
            
            # Make request to update password
            response = auth_client.post(f'/api/users/{user.id}/update-password', json=data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'updated successfully' in data['message'].lower()
            
            # Verify admin_update_password was called with correct arguments
            mock_update_password.assert_called_once_with(
                user.id, 'adminsetpassword'
            )

def test_update_user_password_missing_data(app, auth_client):
    """Test update_user_password endpoint with missing data"""
    with app.app_context():
        # Create a test user
        user = create_user(username='password_update_user')
        
        # Make request without data
        response = auth_client.post(f'/api/users/{user.id}/update-password', json={})
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()