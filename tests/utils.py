import json
from app.utils.db import db

def create_user(username='testuser', password='password123', is_admin=1):
    """
    Create a test user in the database
    
    Args:
        username (str): Username for the test user
        password (str): Password for the test user
        is_admin (int): Whether the user is an admin (1 for admin, 0 for regular user)
        
    Returns:
        UserORM: The created user object
    """
    from app.models.user_orm import UserORM
    
    # Check if user already exists
    existing_user = UserORM.get_by_username(username)
    if existing_user:
        return existing_user
    
    # Create new user
    user = UserORM(
        username=username,
        is_admin=is_admin
    )
    user.set_password(password)
    user_id = user.save()
    
    # Return the created user
    return UserORM.get_by_id(user_id)

def create_script(name='Test Script', description='A test script', 
                  path='/path/to/script.py', parameters=None, user_id=1):
    """
    Create a test script in the database
    
    Args:
        name (str): Name of the script
        description (str): Description of the script
        path (str): Path to the script file
        parameters (str): JSON string of script parameters
        user_id (int): ID of the user creating the script
        
    Returns:
        ScriptORM: The created script object
    """
    from app.models.script_orm import ScriptORM
    
    if parameters is None:
        parameters = json.dumps([{'name': 'test_param', 'default': 'test_value'}])
    
    script = ScriptORM(
        name=name,
        description=description,
        path=path,
        parameters=parameters,
        user_id=user_id
    )
    
    script_id = script.save()
    return ScriptORM.get_by_id(script_id)

def create_aws_profile(name='Test Profile', aws_access_key='test_key', 
                      aws_secret_key='test_secret', region='us-east-1', user_id=1):
    """
    Create a test AWS profile in the database
    
    Args:
        name (str): Name of the AWS profile
        aws_access_key (str): AWS access key
        aws_secret_key (str): AWS secret key
        region (str): AWS region
        user_id (int): ID of the user creating the profile
        
    Returns:
        AWSProfileORM: The created AWS profile object
    """
    from app.models.aws_profile_orm import AWSProfileORM
    
    profile = AWSProfileORM(
        name=name,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        aws_region=region,
        is_default=1
    )
    
    profile_id = profile.save()
    return AWSProfileORM.get_by_id(profile_id)

def login(client, username='testuser', password='password123'):
    """
    Log in a user with the test client
    
    Args:
        client: The Flask test client
        username (str): Username to log in
        password (str): Password for the user
        
    Returns:
        Response: The login response
    """
    # First get the login page to retrieve the CSRF token (if CSRF is enabled)
    with client.application.test_request_context('/login'):
        from flask_wtf.csrf import generate_csrf
        try:
            csrf_token = generate_csrf()
        except:
            # If CSRF is disabled, this will fail silently
            csrf_token = None
    
    data = {
        'username': username,
        'password': password
    }
    
    # Add CSRF token if it was generated
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    return client.post('/login', data=data, follow_redirects=True)

def logout(client):
    """
    Log out a user with the test client
    
    Args:
        client: The Flask test client
        
    Returns:
        Response: The logout response
    """
    # Generate CSRF token if needed
    with client.application.test_request_context('/logout'):
        from flask_wtf.csrf import generate_csrf
        try:
            csrf_token = generate_csrf()
        except:
            # If CSRF is disabled, this will fail silently
            csrf_token = None
    
    # Add CSRF token to headers if it was generated
    headers = {}
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    return client.get('/logout', headers=headers, follow_redirects=True)