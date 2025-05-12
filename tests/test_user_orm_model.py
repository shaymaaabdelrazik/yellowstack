import pytest
import hashlib
import secrets
from datetime import datetime

from app.models.user_orm import UserORM
from app.utils.db import db

def test_user_creation(app):
    """Test creating a new user"""
    with app.app_context():
        # Create a new user
        user = UserORM(
            username='testuser',
            is_admin=1
        )
        user.set_password('password123')
        
        # Save user to database
        user_id = user.save()
        
        # Verify user was created
        assert user_id is not None
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.is_admin == 1
        assert user.password is not None
        assert user.salt is not None
        assert user.created_at is not None

def test_get_by_id(app):
    """Test retrieving a user by ID"""
    with app.app_context():
        # Create test user
        user = UserORM(
            username='testuser',
            is_admin=1
        )
        user.set_password('password123')
        user_id = user.save()
        
        # Retrieve user by ID
        retrieved_user = UserORM.get_by_id(user_id)
        
        # Verify user was retrieved correctly
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.username == 'testuser'
        assert retrieved_user.is_admin == 1

def test_get_by_id_not_found(app):
    """Test retrieving a non-existent user"""
    with app.app_context():
        # Try to retrieve a user with a non-existent ID
        user = UserORM.get_by_id(999)
        
        # Verify no user was found
        assert user is None

def test_get_by_username(app):
    """Test retrieving a user by username"""
    with app.app_context():
        # Create test user
        user = UserORM(
            username='testuser',
            is_admin=1
        )
        user.set_password('password123')
        user.save()
        
        # Retrieve user by username
        retrieved_user = UserORM.get_by_username('testuser')
        
        # Verify user was retrieved correctly
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
        assert retrieved_user.is_admin == 1

def test_get_by_username_not_found(app):
    """Test retrieving a non-existent username"""
    with app.app_context():
        # Try to retrieve a user with a non-existent username
        user = UserORM.get_by_username('nonexistent')
        
        # Verify no user was found
        assert user is None

def test_get_all(app):
    """Test retrieving all users"""
    with app.app_context():
        # Create two test users
        user1 = UserORM(
            username='testuser1',
            is_admin=1
        )
        user1.set_password('password123')
        user1.save()
        
        user2 = UserORM(
            username='testuser2',
            is_admin=0
        )
        user2.set_password('password456')
        user2.save()
        
        # Get all users
        users = UserORM.get_all()

        # Verify that our users are present
        usernames = [user.get('username') for user in users]
        assert 'testuser1' in usernames
        assert 'testuser2' in usernames

def test_password_hashing(app):
    """Test password hashing and verification"""
    with app.app_context():
        # Create a user with a password
        user = UserORM(
            username='testuser',
            is_admin=1
        )
        user.set_password('password123')
        user.save()
        
        # Verify password hashing
        assert user.password is not None
        assert user.salt is not None
        
        # Test password verification
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

def test_hash_password_static_method():
    """Test the static hash_password method"""
    # Test with provided salt
    salt = secrets.token_hex(16)
    password = 'password123'
    
    password_hash, returned_salt = UserORM.hash_password(password, salt)
    
    # Verify hash and salt
    assert password_hash == hashlib.sha256((password + salt).encode()).hexdigest()
    assert returned_salt == salt
    
    # Test with generated salt
    password_hash, generated_salt = UserORM.hash_password(password)
    
    # Verify hash and generated salt
    assert password_hash == hashlib.sha256((password + generated_salt).encode()).hexdigest()
    assert generated_salt is not None
    assert len(generated_salt) == 32  # 16 bytes = 32 hex characters

def test_verify_password_static_method():
    """Test the static verify_password method"""
    password = 'password123'
    salt = secrets.token_hex(16)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Test verification with correct password
    assert UserORM.verify_password(hashed_password, salt, password) is True
    
    # Test verification with incorrect password
    assert UserORM.verify_password(hashed_password, salt, 'wrongpassword') is False

def test_save_new(app):
    """Test saving a new user"""
    with app.app_context():
        # Create a new user
        user = UserORM(
            username='newuser',
            is_admin=0
        )
        user.set_password('newpassword')
        
        # Save the user
        user_id = user.save()
        
        # Verify user was saved correctly
        assert user_id is not None
        
        # Retrieve user from database
        saved_user = UserORM.get_by_id(user_id)
        assert saved_user is not None
        assert saved_user.username == 'newuser'
        assert saved_user.is_admin == 0

def test_save_update(app):
    """Test updating an existing user"""
    with app.app_context():
        # Create and save a user
        user = UserORM(
            username='testuser',
            is_admin=0
        )
        user.set_password('password123')
        user_id = user.save()
        
        # Update the user
        user.username = 'updated_username'
        user.save()
        
        # Verify user was updated
        updated_user = UserORM.get_by_id(user_id)
        assert updated_user.username == 'updated_username'

def test_toggle_admin(app):
    """Test toggling admin status"""
    with app.app_context():
        # Create a regular user
        user = UserORM(
            username='testuser',
            is_admin=0
        )
        user.set_password('password123')
        user_id = user.save()
        
        # Verify initial admin status
        assert user.is_admin == 0
        
        # Toggle admin status to 1
        user.toggle_admin(1)
        
        # Verify admin status was updated
        assert user.is_admin == 1
        
        # Verify in database
        updated_user = UserORM.get_by_id(user_id)
        assert updated_user.is_admin == 1
        
        # Toggle admin status back to 0
        user.toggle_admin(0)
        
        # Verify admin status was updated
        assert user.is_admin == 0
        
        # Verify in database
        updated_user = UserORM.get_by_id(user_id)
        assert updated_user.is_admin == 0

def test_delete(app):
    """Test deleting a user"""
    with app.app_context():
        # Create a user
        user = UserORM(
            username='testuser',
            is_admin=0
        )
        user.set_password('password123')
        user_id = user.save()
        
        # Verify user exists
        assert UserORM.get_by_id(user_id) is not None
        
        # Delete the user
        result = user.delete()
        
        # Verify deletion was successful
        assert result is True
        
        # Verify user no longer exists
        assert UserORM.get_by_id(user_id) is None

def test_exists(app):
    """Test checking if a username exists"""
    with app.app_context():
        # Create a user
        user = UserORM(
            username='testuser',
            is_admin=0
        )
        user.set_password('password123')
        user.save()
        
        # Check existing username
        assert UserORM.exists('testuser') is True
        
        # Check non-existent username
        assert UserORM.exists('nonexistent') is False

def test_to_dict(app):
    """Test converting user to dictionary"""
    with app.app_context():
        # Create a user
        user = UserORM(
            username='testuser',
            is_admin=1
        )
        user.set_password('password123')
        user.save()
        
        # Get dictionary representation
        user_dict = user.to_dict()
        
        # Verify dictionary contains expected fields
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'is_admin' in user_dict
        assert 'created_at' in user_dict
        
        # Verify values are correct
        assert user_dict['username'] == 'testuser'
        assert user_dict['is_admin'] == 1
        
        # Verify sensitive info is not included by default
        assert 'password' not in user_dict
        assert 'salt' not in user_dict
        
        # Get dictionary with sensitive info
        user_dict_sensitive = user.to_dict(include_sensitive=True)
        
        # Verify sensitive info is included
        assert 'password' in user_dict_sensitive
        assert 'salt' in user_dict_sensitive