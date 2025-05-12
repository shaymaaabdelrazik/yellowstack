"""
Tests for CSRF protection verification
"""
import pytest
from flask import session
from bs4 import BeautifulSoup
from flask_wtf.csrf import CSRFProtect

# Import fixtures directly from conftest_csrf.py
from tests.conftest_csrf import csrf_app, csrf_client, csrf_auth_client

# Use marker for organization
pytestmark = pytest.mark.csrf

def test_csrf_enabled_in_config(csrf_app):
    """Check that CSRF protection is enabled in configuration"""
    assert csrf_app.config.get('WTF_CSRF_ENABLED') is True
    assert csrf_app.config.get('WTF_CSRF_SECRET_KEY') == 'csrf_test_key'

def test_csrf_instance_initialized(csrf_app):
    """Check that CSRFProtect instance is initialized"""
    # Check that extension is properly imported and initialized
    extensions = csrf_app.extensions
    assert 'csrf' in extensions, "CSRF protection is not in app extensions"
    assert isinstance(extensions['csrf'], CSRFProtect), "CSRF extension is not an instance of CSRFProtect"

def test_csrf_token_in_login_page(csrf_client):
    """Check CSRF token presence on login page"""
    response = csrf_client.get('/login')
    assert response.status_code == 200
    
    # Use BeautifulSoup to parse HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for the presence of a hidden CSRF token field
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    assert csrf_input is not None, "CSRF token input field not found in login page"
    assert csrf_input.get('type') == 'hidden', "CSRF token input is not hidden"
    assert csrf_input.get('value'), "CSRF token value is empty"

    # Check for the presence of a meta tag with CSRF token
    meta_csrf = soup.find('meta', {'name': 'csrf-token'})
    assert meta_csrf is not None, "CSRF token meta tag not found"
    assert meta_csrf.get('content'), "CSRF token meta content is empty"

def test_login_without_csrf_token(csrf_client):
    """Check that login without CSRF token fails"""
    response = csrf_client.post('/login', data={
        'username': 'admin',
        'password': 'password'
    })
    
    # Expect 400 Bad Request error when CSRF token is missing
    assert response.status_code == 400, "Login without CSRF token should fail with 400 status"
    
    # Check that the user is not authenticated
    with csrf_client.session_transaction() as session:
        assert 'user_id' not in session, "User should not be authenticated without CSRF token"

def test_login_with_invalid_csrf_token(csrf_client):
    """Check that login with invalid CSRF token fails"""
    response = csrf_client.post('/login', data={
        'username': 'admin',
        'password': 'password',
        'csrf_token': 'invalid_token'
    })
    
    # Expect 400 Bad Request error with invalid CSRF token
    assert response.status_code == 400, "Login with invalid CSRF token should fail with 400 status"
    
    # Check that the user is not authenticated
    with csrf_client.session_transaction() as session:
        assert 'user_id' not in session, "User should not be authenticated with invalid CSRF token"

def test_login_with_valid_csrf_token(csrf_client):
    """Check that login with valid CSRF token succeeds"""
    # First get CSRF token from the page
    response = csrf_client.get('/login')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')
    assert csrf_token, "Could not find CSRF token"
    
    # Now use this token to log in
    # Use csrf_admin user that was created in conftest_csrf.py
    response = csrf_client.post('/login', data={
        'username': 'csrf_admin',
        'password': 'password',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Check that login is successful
    assert response.status_code == 200
    
    # Check that the user is authenticated
    with csrf_client.session_transaction() as session:
        assert 'user_id' in session, "User should be authenticated after successful login"
        
def test_meta_csrf_token_in_layout(csrf_client):
    """Check for CSRF token meta tag in layout for AJAX requests"""
    # Check on a page that requires authentication
    # First log in
    response = csrf_client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')
    
    csrf_client.post('/login', data={
        'username': 'csrf_admin',
        'password': 'password',
        'csrf_token': csrf_token
    })
    
    # Now check the page that uses layout.html
    response = csrf_client.get('/scripts')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    meta_csrf = soup.find('meta', {'name': 'csrf-token'})
    assert meta_csrf is not None, "CSRF token meta tag not found in authenticated layout"
    assert meta_csrf.get('content'), "CSRF token meta content is empty in authenticated layout"
    
    # Check if csrf-protection.js script is included
    csrf_script = soup.find('script', {'src': lambda x: x and 'csrf-protection.js' in x})
    assert csrf_script is not None, "CSRF protection JavaScript not included in layout"