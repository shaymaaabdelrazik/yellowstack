from flask import Blueprint, request, jsonify, session
from app.services import auth_service
from functools import wraps
import logging

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
user_api = Blueprint('user_api', __name__, url_prefix='/api/users')

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and is an admin
        if not session.get('is_admin'):
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Admin access required'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

# Get all users (admin only)
@user_api.route('', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)"""
    users = auth_service.get_all_users()
    
    return jsonify({
        'success': True,
        'users': users
    })

# Add a new user (admin only)
@user_api.route('', methods=['POST'])
@admin_required
def add_user():
    """Add a new user (admin only)"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        }), 400
    
    # Create a new user
    username = data.get('username')
    password = data.get('password')
    is_admin = 1 if data.get('is_admin') else 0
    
    success, result = auth_service.create_user(username, password, is_admin)
    
    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 400
    
    # Log user creation
    logger.info(f"Admin {session.get('username')} created user {username}")
    
    return jsonify({
        'success': True,
        'user_id': result
    })

# Get current user's profile
@user_api.route('/profile', methods=['GET'])
def get_user_profile():
    """Get current user's profile information"""
    user = auth_service.get_current_user()
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

# Delete a user (admin only)
@user_api.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    # Get current user ID
    current_user_id = session.get('user_id')
    
    # Try to delete the user
    success, message = auth_service.delete_user(user_id, current_user_id)
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    # Get user information for logging
    user = auth_service.user_adapter.get_by_id(user_id)
    if user:
        username = user.username
    else:
        username = f"ID: {user_id}"
    
    # Log user deletion
    logger.info(f"Admin {session.get('username')} deleted user {username}")
    
    return jsonify({
        'success': True,
        'message': 'User deleted successfully'
    })

# Toggle admin status for a user (admin only)
@user_api.route('/<int:user_id>/admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user (admin only)"""
    data = request.json
    if data is None or 'is_admin' not in data:
        return jsonify({
            'success': False,
            'message': 'is_admin field is required'
        }), 400
    
    # Update admin status
    is_admin = 1 if data.get('is_admin') else 0
    success, message = auth_service.toggle_admin(user_id, is_admin)
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    # Get user information for logging
    user = auth_service.user_adapter.get_by_id(user_id)
    if user:
        username = user.username
    else:
        username = f"ID: {user_id}"
    
    # Log admin status change
    action = "granted" if is_admin else "revoked"
    logger.info(f"Admin {session.get('username')} {action} admin privileges for user {username}")
    
    return jsonify({
        'success': True,
        'message': f"Admin status {'granted' if is_admin else 'revoked'} successfully"
    })

# Change current user's password
@user_api.route('/change_password', methods=['POST'])
def change_password():
    """Change current user's password"""
    data = request.json
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({
            'success': False,
            'message': 'Current password and new password are required'
        }), 400
    
    # Get current user ID
    user_id = session.get('user_id')
    
    # Change password
    success, message = auth_service.change_password(
        user_id, 
        data.get('current_password'), 
        data.get('new_password')
    )
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    # Log password change
    logger.info(f"User {session.get('username')} changed their password")
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })

# Update user password by admin
@user_api.route('/<int:user_id>/update-password', methods=['POST'])
@admin_required
def update_user_password(user_id):
    """Update a user's password (admin only)"""
    data = request.json
    
    if not data or not data.get('new_password'):
        return jsonify({
            'success': False,
            'message': 'New password is required'
        }), 400
    
    # Update password
    success, message = auth_service.admin_update_password(
        user_id,
        data.get('new_password')
    )
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    # Get user information for logging
    user = auth_service.user_adapter.get_by_id(user_id)
    if user:
        username = user.username
    else:
        username = f"ID: {user_id}"
    
    # Log password update
    logger.info(f"Admin {session.get('username')} changed password for user {username}")
    
    return jsonify({
        'success': True,
        'message': 'Password updated successfully'
    })