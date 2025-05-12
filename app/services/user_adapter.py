import logging
from app.models import UserORM

logger = logging.getLogger('yellowstack')

class UserAdapter:
    """
    Adapter class for the SQLAlchemy ORM User model.
    This provides a standardized interface for all user operations.
    """
    
    def __init__(self):
        """
        Initialize the adapter
        """
        self.use_orm = True  # Always True, kept for backward compatibility
    
    def get_by_id(self, user_id):
        """Get a user by ID"""
        return UserORM.get_by_id(user_id)
    
    def get_by_username(self, username):
        """Get a user by username"""
        return UserORM.get_by_username(username)
    
    def get_all(self):
        """Get all users"""
        return UserORM.get_all()
    
    def exists(self, username):
        """Check if a user with the given username exists"""
        return UserORM.exists(username)
    
    def create(self, username, password, is_admin=0):
        """Create a new user"""
        # Create user using ORM
        orm_user = UserORM(
            username=username,
            is_admin=is_admin
        )
        orm_user.set_password(password)
        user_id = orm_user.save()
        
        logger.debug(f"Created user {username}")
        return user_id
    
    def delete(self, user_id):
        """Delete a user"""
        orm_user = UserORM.get_by_id(user_id)
        if orm_user:
            success = orm_user.delete()
        else:
            success = False
        
        return success
    
    def toggle_admin(self, user_id, is_admin):
        """Toggle admin status for a user"""
        orm_user = UserORM.get_by_id(user_id)
        if orm_user:
            success = orm_user.toggle_admin(1 if is_admin else 0)
        else:
            success = False
        
        return success
    
    def check_password(self, user, password):
        """Check if the provided password is correct"""
        # Handle case where we are passed a model instance
        if isinstance(user, UserORM):
            return user.check_password(password)
        
        # Otherwise, look up the user
        orm_user = UserORM.get_by_id(user) if isinstance(user, int) else UserORM.get_by_username(user)
        if orm_user:
            return orm_user.check_password(password)
        
        return False
    
    def set_password(self, user_id, new_password):
        """Set a new password for the user"""
        orm_user = UserORM.get_by_id(user_id)
        if orm_user:
            orm_user.set_password(new_password)
            success = orm_user.save()
        else:
            success = False
        
        return success

# Create a default instance that can be imported directly
user_adapter = UserAdapter()