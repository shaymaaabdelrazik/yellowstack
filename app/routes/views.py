from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
import os
from datetime import datetime
from functools import wraps
from app.models import UserORM

# Create blueprint
views = Blueprint('views', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            # Save requested URL for redirect after login
            session['next_url'] = request.path
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('views.login'))
        
        # Additional check for user validity
        user = UserORM.get_by_id(session['user_id'])
        
        if not user:
            # Session refers to a user that no longer exists
            session.clear()
            flash('Your session has expired. Please log in again', 'warning')
            return redirect(url_for('views.login'))
            
        return f(*args, **kwargs)
    return decorated_function

# Home/Dashboard page
@views.route('/')
@login_required
def index():
    """Render the home page dashboard"""
    return render_template('index.html')

# Login page
@views.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = UserORM.get_by_username(username)
        
        if user and user.check_password(password):
            # Set up user session
            session.clear()  # Clear existing session data
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session.permanent = True
            
            # Force save session
            session.modified = True
            
            # Log the successful login
            # logger.info(f"User {username} logged in successfully")
            
            # Redirect to requested page or to dashboard
            next_page = session.pop('next_url', None)
            return redirect(next_page or url_for('views.index'))
        
        # Log failed login attempt
        # logger.warning(f"Failed login attempt for user {username}")
        return render_template('login.html', error='Invalid username or password')
    
    # GET request - show login form
    return render_template('login.html')

# Logout route
@views.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('username', 'Unknown')
    
    # Clear session
    session.clear()
    
    # Log the logout
    # logger.info(f"User {username} logged out")
    
    # Redirect to login page
    return redirect(url_for('views.login'))

# Scripts management page
@views.route('/scripts')
@login_required
def scripts():
    """Render the scripts management page"""
    return render_template('scripts.html')

# Execution history page
@views.route('/execution_history')
@login_required
def execution_history():
    """Render the execution history page"""
    return render_template('execution_history.html')

# Execution details page
@views.route('/execution_details/<int:execution_id>')
@login_required
def execution_details(execution_id):
    """Render the execution details page with improved error handling"""
    try:
        # Check if the record exists in the database using ORM
        from app.models import ExecutionORM
        
        # Check if execution exists
        execution = ExecutionORM.get_by_id_with_details(execution_id)
        
        if not execution:
            # If record not found, redirect to execution history
            flash('Execution record not found', 'error')
            return redirect('/execution_history')

        # Add CSS styles for expanding the block
        st_markdown = """
        <style>
            /* Global overrides for execution details section */
            .execution-details-container {
                max-width: 100% !important;
                width: 100% !important;
                padding: 15px;
                border-radius: 5px;
            }

            .execution-details-container h2 {
                margin-bottom: 20px;
                font-size: 1.8rem;
            }

            /* Ensure text wrapping in code blocks */
            pre {
                white-space: pre-wrap !important;
                word-wrap: break-word !important;
                max-width: 100% !important;
                width: 100% !important;
            }

            .execution-details-header {
                padding: 10px 0;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(150, 150, 150, 0.2);
                width: 100% !important;
            }
        </style>
        """

        # Render template with aggressive CSS styles, pass execution_id and current time
        return render_template(
            'execution_details.html',
            styles=st_markdown,
            execution_id=execution_id,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    except Exception as e:
        # Log error and return to list
        print(f"Error rendering execution details page for ID {execution_id}: {e}")
        flash(f"Error loading execution details: {e}", 'error')
        return redirect('/execution_history')

# Viewing execution (alternate route to execution_details)
@views.route('/view_execution/<int:execution_id>')
@login_required
def view_execution(execution_id):
    """New route for viewing execution details"""
    try:
        print(f">>> Request to view execution ID={execution_id}")
        # Check if the record exists using ORM
        from app.models import ExecutionORM
        
        # Get execution
        execution = ExecutionORM.get_by_id(execution_id)
        
        if not execution:
            flash('Execution record not found', 'error')
            return redirect('/execution_history')
        
        # Add CSS styles
        st_markdown = """
        <style>
            /* Styles for execution details */
            .execution-details-container {
                max-width: 100% !important;
                width: 100% !important;
                padding: 15px;
                border-radius: 5px;
            }

            .execution-details-container h2 {
                margin-bottom: 20px;
                font-size: 1.8rem;
            }

            /* Ensure text wrapping in code blocks */
            pre {
                white-space: pre-wrap !important;
                word-wrap: break-word !important;
                max-width: 100% !important;
                width: 100% !important;
            }

            .execution-details-header {
                padding: 10px 0;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(150, 150, 150, 0.2);
                width: 100% !important;
            }
        </style>
        """
        
        # Return the same template as execution_details but with different route
        return render_template('execution_details.html', 
                              styles=st_markdown, 
                              execution_id=execution_id,
                              now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        print(f"Error in view_execution: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect('/execution_history')

# Settings page
@views.route('/settings')
@login_required
def settings():
    """Render the settings page"""
    return render_template('settings.html')

# Scheduler page
@views.route('/scheduler')
@login_required
def scheduler():
    """Render the scheduler page"""
    return render_template('scheduler.html')

# User management page (admin only)
@views.route('/users')
@login_required
def users():
    """Render the user management page (admin only)"""
    # Check if the current user is an admin
    if not session.get('is_admin'):
        flash('Access denied: Administrator privileges required', 'danger')
        return redirect(url_for('views.index'))
    
    return render_template('users.html')

# Favicon
@views.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(views.root_path, '..', 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Test session route (for debugging)
@views.route('/test_session')
def test_session():
    """Test route for checking session handling"""
    from flask import current_app
    output = []
    output.append(f"Session contents: {dict(session)}")
    output.append(f"Session cookies configured with: Secure={current_app.config['SESSION_COOKIE_SECURE']}, HttpOnly={current_app.config['SESSION_COOKIE_HTTPONLY']}")
    return "<br>".join(output)