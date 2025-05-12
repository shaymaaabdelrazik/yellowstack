import logging
from flask import session, request, redirect, url_for, flash
from functools import wraps
from app.services.user_adapter import user_adapter

logger = logging.getLogger('yellowstack')

class AuthService:
    """Service for handling authentication and user management using the ORM adapter"""
    
    def __init__(self, use_orm=True):
        """
        Initialize the auth service
        """
        self.user_adapter = user_adapter
        self.user_adapter.use_orm = True
    
    def login(self, username, password):
        """Authenticate a user and create a session"""
        user = self.user_adapter.get_by_username(username)
        
        if not user:
            logger.warning(f"Login failed: user {username} not found")
            return False, "Invalid username or password"
        
        if not self.user_adapter.check_password(user, password):
            logger.warning(f"Login failed: invalid password for user {username}")
            return False, "Invalid username or password"
        
        # Create session
        session.clear()  # Clear any existing session data
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        session.permanent = True
        session.modified = True
        
        logger.info(f"User {username} logged in successfully")
        return True, None
    
    def logout(self):
        """End a user's session"""
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        return True
    
    def get_current_user(self):
        """Get the currently logged in user"""
        user_id = session.get('user_id')
        if not user_id:
            return None
            
        return self.user_adapter.get_by_id(user_id)
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password"""
        user = self.user_adapter.get_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not self.user_adapter.check_password(user, current_password):
            logger.warning(f"Password change failed: incorrect current password for user {user.username}")
            return False, "Current password is incorrect"
        
        # Set new password
        success = self.user_adapter.set_password(user_id, new_password)
        
        if success:
            logger.info(f"Password changed for user {user.username}")
            return True, None
        else:
            logger.warning(f"Password change failed for user {user.username}")
            return False, "Failed to update password"
    
    def admin_update_password(self, user_id, new_password):
        """Update a user's password (admin only)"""
        user = self.user_adapter.get_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Set new password
        success = self.user_adapter.set_password(user_id, new_password)
        
        if success:
            logger.info(f"Password updated for user {user.username} by admin")
            return True, None
        else:
            logger.warning(f"Password update by admin failed for user {user.username}")
            return False, "Failed to update password"
    
    def get_all_users(self):
        """Get all users (admin only)"""
        return self.user_adapter.get_all()
    
    def create_user(self, username, password, is_admin=0):
        """Create a new user (admin only)"""
        # Check if user exists
        if self.user_adapter.exists(username):
            return False, "A user with this username already exists"
        
        # Create new user
        user_id = self.user_adapter.create(username, password, is_admin)
        
        logger.info(f"User created: {username} (ID: {user_id})")
        return True, user_id
    
    def delete_user(self, user_id, current_user_id):
        """Delete a user (admin only)"""
        # Cannot delete yourself
        if user_id == current_user_id:
            return False, "You cannot delete your own account"
        
        user = self.user_adapter.get_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Delete the user
        success = self.user_adapter.delete(user_id)
        
        if success:
            logger.info(f"User deleted: {user.username} (ID: {user_id})")
        else:
            logger.warning(f"User deletion failed: {user.username} (ID: {user_id})")
            
        return success, None
    
    def toggle_admin(self, user_id, is_admin):
        """Toggle admin status for a user (admin only)"""
        user = self.user_adapter.get_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Update admin status
        success = self.user_adapter.toggle_admin(user_id, 1 if is_admin else 0)
        
        if success:
            action = "granted" if is_admin else "revoked"
            logger.info(f"Admin privileges {action} for user {user.username} (ID: {user_id})")
            return True, None
        else:
            logger.warning(f"Admin toggle failed for user {user.username} (ID: {user_id})")
            return False, "Failed to update admin status"
    
    def login_required(self, f):
        """Decorator for routes that require login"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                # Save requested URL for redirect after login
                session['next_url'] = request.path
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('views.login'))
            
            # Additional check for user validity
            user = self.user_adapter.get_by_id(session['user_id'])
            
            if not user:
                # Session refers to a user that no longer exists
                session.clear()
                flash('Your session has expired. Please log in again', 'warning')
                return redirect(url_for('views.login'))
                
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(self, f):
        """Decorator for routes that require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in and is an admin
            if not session.get('is_admin'):
                flash('Access denied: Administrator privileges required', 'danger')
                return redirect(url_for('views.index'))
                
            return f(*args, **kwargs)
        return decorated_function

# Create an instance using ORM mode
auth_service = AuthService()