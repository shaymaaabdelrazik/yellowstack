from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging

# Get the existing logger from the application
logger = logging.getLogger('yellowstack')

def login_required(f):
    """
    Decorator for routes that require user login.
    
    Checks if a user is logged in and redirects to the login page
    if not. Also saves the requested URL for redirect after login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            # Save requested URL for redirect after login
            session['next_url'] = request.path
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('views.login'))
        
        # Additional check for user validity
        from app.models import UserORM
        user = UserORM.get_by_id(session['user_id'])
        
        if not user:
            # Session refers to a user that no longer exists
            session.clear()
            flash('Your session has expired. Please log in again', 'warning')
            return redirect(url_for('views.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator for routes that require admin privileges.
    
    Only allows access if the current user is an admin.
    Redirects to the home page with an error message otherwise.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and is an admin
        if not session.get('is_admin'):
            flash('Access denied: Administrator privileges required', 'danger')
            return redirect(url_for('views.index'))
                
        return f(*args, **kwargs)
    return decorated_function