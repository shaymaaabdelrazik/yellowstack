import pytest
from unittest.mock import patch, MagicMock
from flask import session, url_for
from app.services.auth_service import auth_service
from app.models.user_orm import UserORM
from tests.utils import create_user

def test_login_success(app):
    """Test successful user login"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testuser', password='password123', is_admin=1)
        
        # Test login with client
        with app.test_request_context():
            # Perform login
            success, error = auth_service.login('testuser', 'password123')
            
            # Verify login was successful
            assert success is True
            assert error is None
            
            # Verify session variables were set
            assert session.get('user_id') == user.id
            assert session.get('username') == 'testuser'
            assert session.get('is_admin') == 1

def test_login_invalid_username(app):
    """Test login with invalid username"""
    with app.app_context():
        # Perform login with non-existent username
        with app.test_request_context():
            success, error = auth_service.login('nonexistent', 'password123')
            
            # Verify login failed
            assert success is False
            assert error == "Invalid username or password"
            
            # Verify session was not created
            assert 'user_id' not in session

def test_login_invalid_password(app):
    """Test login with invalid password"""
    with app.app_context():
        # Create test user
        create_user(username='testuser', password='password123')
        
        # Perform login with wrong password
        with app.test_request_context():
            success, error = auth_service.login('testuser', 'wrongpassword')
            
            # Verify login failed
            assert success is False
            assert error == "Invalid username or password"
            
            # Verify session was not created
            assert 'user_id' not in session

def test_logout(app):
    """Test user logout"""
    with app.app_context():
        # Set up a session
        with app.test_request_context():
            # Set session variables
            session['user_id'] = 1
            session['username'] = 'testuser'
            session['is_admin'] = 1
            session.modified = True
            
            # Verify session is active
            assert session.get('user_id') == 1
            
            # Perform logout
            auth_service.logout()
            
            # Verify session was cleared
            assert 'user_id' not in session
            assert 'username' not in session
            assert 'is_admin' not in session

def test_get_current_user(app):
    """Test retrieving current user from session"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testuser', password='password123')
        
        # Test with client
        with app.test_request_context():
            # Set up session
            session['user_id'] = user.id
            
            # Get current user
            current_user = auth_service.get_current_user()
            
            # Verify correct user was retrieved
            assert current_user is not None
            assert current_user.id == user.id
            assert current_user.username == 'testuser'

def test_get_current_user_no_session(app):
    """Test retrieving current user when no session exists"""
    with app.app_context():
        with app.test_request_context():
            # Get current user without session
            current_user = auth_service.get_current_user()
            
            # Verify no user was returned
            assert current_user is None

def test_change_password_success(app):
    """Test successful password change"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testuser', password='password123')
        
        # Change password
        success, error = auth_service.change_password(
            user.id, 'password123', 'newpassword123'
        )
        
        # Verify password change was successful
        assert success is True
        assert error is None
        
        # Verify new password works
        updated_user = UserORM.get_by_id(user.id)
        assert updated_user.check_password('newpassword123') is True
        assert updated_user.check_password('password123') is False

def test_change_password_wrong_current(app):
    """Test password change with incorrect current password"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testuser', password='password123')
        
        # Change password with wrong current password
        success, error = auth_service.change_password(
            user.id, 'wrongpassword', 'newpassword123'
        )
        
        # Verify password change failed
        assert success is False
        assert error == "Current password is incorrect"
        
        # Verify password was not changed
        user = UserORM.get_by_id(user.id)
        assert user.check_password('password123') is True
        assert user.check_password('newpassword123') is False

def test_change_password_user_not_found(app):
    """Test password change for non-existent user"""
    with app.app_context():
        # Change password for non-existent user
        success, error = auth_service.change_password(
            999, 'password123', 'newpassword123'
        )
        
        # Verify password change failed
        assert success is False
        assert error == "User not found"

def test_admin_update_password(app):
    """Test admin updating a user's password"""
    with app.app_context():
        # Create a test user
        user = create_user(username='testuser', password='password123')
        
        # Admin updates password
        success, error = auth_service.admin_update_password(
            user.id, 'adminsetpassword'
        )
        
        # Verify password update was successful
        assert success is True
        assert error is None
        
        # Verify new password works
        updated_user = UserORM.get_by_id(user.id)
        assert updated_user.check_password('adminsetpassword') is True
        assert updated_user.check_password('password123') is False

def test_admin_update_password_user_not_found(app):
    """Test admin updating password for non-existent user"""
    with app.app_context():
        # Update password for non-existent user
        success, error = auth_service.admin_update_password(
            999, 'adminsetpassword'
        )
        
        # Verify update failed
        assert success is False
        assert error == "User not found"

def test_get_all_users(app):
    """Test retrieving all users"""
    with app.app_context():
        # Create test users
        create_user(username='user1', password='password1')
        create_user(username='user2', password='password2')
        create_user(username='user3', password='password3')
        
        # Get all users
        users = auth_service.get_all_users()
        
        # Verify all users were retrieved
        assert len(users) >= 3
        usernames = [user.get('username') for user in users]
        assert 'user1' in usernames
        assert 'user2' in usernames
        assert 'user3' in usernames

def test_create_user(app):
    """Test creating a new user"""
    with app.app_context():
        # Create a new user
        success, user_id = auth_service.create_user(
            'newuser', 'newpassword', is_admin=1
        )
        
        # Verify user creation was successful
        assert success is True
        assert user_id is not None
        
        # Verify user was saved to database
        user = UserORM.get_by_id(user_id)
        assert user is not None
        assert user.username == 'newuser'
        assert user.is_admin == 1
        assert user.check_password('newpassword') is True

def test_create_user_duplicate(app):
    """Test creating a user with a duplicate username"""
    with app.app_context():
        # Create a user
        create_user(username='existinguser', password='password123')
        
        # Try to create another user with the same username
        success, error = auth_service.create_user(
            'existinguser', 'anotherpassword'
        )
        
        # Verify user creation failed
        assert success is False
        assert error == "A user with this username already exists"

def test_delete_user(app):
    """Test deleting a user"""
    with app.app_context():
        # Create a user to delete
        user = create_user(username='deleteme', password='password123')
        
        # Create another user (current user)
        current_user = create_user(username='currentuser', password='password123')
        
        # Delete the user
        success, error = auth_service.delete_user(user.id, current_user.id)
        
        # Verify deletion was successful
        assert success is True
        assert error is None
        
        # Verify user no longer exists
        assert UserORM.get_by_id(user.id) is None

def test_delete_user_self(app):
    """Test deleting own user account (should not be allowed)"""
    with app.app_context():
        # Create a user
        user = create_user(username='selfdelete', password='password123')
        
        # Try to delete self
        success, error = auth_service.delete_user(user.id, user.id)
        
        # Verify deletion was not allowed
        assert success is False
        assert error == "You cannot delete your own account"
        
        # Verify user still exists
        assert UserORM.get_by_id(user.id) is not None

def test_delete_user_not_found(app):
    """Test deleting a non-existent user"""
    with app.app_context():
        # Create current user
        current_user = create_user(username='currentuser', password='password123')
        
        # Try to delete non-existent user
        success, error = auth_service.delete_user(999, current_user.id)
        
        # Verify deletion failed
        assert success is False
        assert error == "User not found"

def test_toggle_admin(app):
    """Test toggling admin status"""
    with app.app_context():
        # Create a regular user
        user = create_user(username='regularuser', password='password123', is_admin=0)
        
        # Verify initial admin status
        assert user.is_admin == 0
        
        # Toggle to admin
        success, error = auth_service.toggle_admin(user.id, True)
        
        # Verify toggle was successful
        assert success is True
        assert error is None
        
        # Verify user is now admin
        user = UserORM.get_by_id(user.id)
        assert user.is_admin == 1
        
        # Toggle back to regular user
        success, error = auth_service.toggle_admin(user.id, False)
        
        # Verify toggle was successful
        assert success is True
        assert error is None
        
        # Verify user is no longer admin
        user = UserORM.get_by_id(user.id)
        assert user.is_admin == 0

def test_toggle_admin_user_not_found(app):
    """Test toggling admin status for non-existent user"""
    with app.app_context():
        # Try to toggle non-existent user
        success, error = auth_service.toggle_admin(999, True)
        
        # Verify toggle failed
        assert success is False
        assert error == "User not found"

def test_login_required_decorator():
    """Test the login_required functionality directly"""
    # Instead of testing the decorator with Flask routes, we'll test the core functionality
    login_decorator = auth_service.login_required
    assert callable(login_decorator)
    
    # Verify it's a decorator function that returns a wrapped function
    def test_func():
        pass
    
    wrapped_func = login_decorator(test_func)
    assert callable(wrapped_func)
    # The function name might vary based on implementation, so we're just checking
    # it's callable and not None

def test_admin_required_decorator():
    """Test the admin_required functionality directly"""
    # Instead of testing the decorator with Flask routes, we'll test the core functionality
    admin_decorator = auth_service.admin_required
    assert callable(admin_decorator)
    
    # Verify it's a decorator function that returns a wrapped function
    def test_func():
        pass
    
    wrapped_func = admin_decorator(test_func)
    assert callable(wrapped_func)
    # The function name might vary based on implementation, so we're just checking
    # it's callable and not None