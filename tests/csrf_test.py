#!/usr/bin/env python3
"""
Comprehensive script for testing CSRF protection in the YellowStack application.
"""
import requests
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Base URL of your application
base_url = 'https://yellowstack.cheesebanana.com'

# Create a session with SSL verification disabled for self-signed certificates
session = requests.Session()
session.verify = False

# More completely suppress InsecureRequestWarning warnings
import urllib3
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Completely suppress the InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
urllib3.disable_warnings(InsecureRequestWarning)

def test_login_without_csrf():
    """Test login without CSRF token."""
    try:
        response = session.post(
            urljoin(base_url, '/login'),
            data={'username': 'admin', 'password': 'password'}
        )
        print(f"Login without CSRF token: Status code {response.status_code}")
        print(f"Response: {response.text[:100] if response.text else 'Empty response'}...")
        assert response.status_code == 400, "Login without CSRF token should fail with 400 status"
    except Exception as e:
        print(f"Error testing login without CSRF: {e}")
        assert False, f"Test failed with exception: {e}"

def test_login_with_invalid_csrf():
    """Test login with invalid CSRF token."""
    try:
        response = session.post(
            urljoin(base_url, '/login'),
            data={
                'username': 'admin', 
                'password': 'password',
                'csrf_token': 'invalid_fake_token'
            }
        )
        print(f"Login with invalid CSRF token: Status code {response.status_code}")
        print(f"Response: {response.text[:100] if response.text else 'Empty response'}...")
        assert response.status_code == 400, "Login with invalid CSRF token should fail with 400 status"
    except Exception as e:
        print(f"Error testing login with invalid CSRF: {e}")
        assert False, f"Test failed with exception: {e}"

def test_api_without_csrf():
    """Test API endpoint without CSRF token."""
    try:
        response = session.post(
            urljoin(base_url, '/api/users'),
            json={'username': 'test_user', 'password': 'password'}
        )
        print(f"API call without CSRF token: Status code {response.status_code}")
        print(f"Response: {response.text[:100] if response.text else 'Empty response'}...")
        assert response.status_code == 400, "API call without CSRF token should fail with 400 status"
    except Exception as e:
        print(f"Error testing API without CSRF: {e}")
        assert False, f"Test failed with exception: {e}"

def extract_csrf_token(html_content):
    """Extract CSRF token from HTML content."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find token in input field
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input and csrf_input.get('value'):
            return csrf_input.get('value')
        
        # Try to find token in meta tag
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta and csrf_meta.get('content'):
            return csrf_meta.get('content')
        
        print("Could not find CSRF token in the page")
        return None
    except Exception as e:
        print(f"Error extracting CSRF token: {e}")
        return None

def test_login_with_valid_csrf():
    """Test login with valid CSRF token."""
    try:
        # Get login page to get CSRF token
        login_response = session.get(urljoin(base_url, '/login'))
        if login_response.status_code != 200:
            print(f"Failed to get login page: {login_response.status_code}")
            assert False, f"Failed to get login page: {login_response.status_code}"
        
        # Extract CSRF token
        csrf_token = extract_csrf_token(login_response.text)
        if not csrf_token:
            assert False, "Failed to extract CSRF token from login page"
        
        print(f"Extracted valid CSRF token: {csrf_token[:15]}...")
        
        # Try login with valid token and proper Referer header
        response = session.post(
            urljoin(base_url, '/login'),
            data={
                'username': 'admin',
                'password': 'password',
                'csrf_token': csrf_token
            },
            headers={
                'Referer': urljoin(base_url, '/login')
            }
        )
        print(f"Login with valid CSRF token: Status code {response.status_code}")
        print(f"Response: {response.text[:100] if response.text else 'Empty response'}...")
        
        # Login should succeed with a 200 status code or redirect (302)
        assert response.status_code in [200, 302], "Login with valid CSRF token should succeed"
    except Exception as e:
        print(f"Error testing login with valid CSRF: {e}")
        assert False, f"Test failed with exception: {e}"

def test_multiple_api_endpoints():
    """Test CSRF protection on multiple API endpoints."""
    # Get a valid CSRF token first
    try:
        # Since we might be logged in from previous tests, let's get a page
        response = session.get(urljoin(base_url, '/'))
        if response.status_code != 200:
            print(f"Failed to get page for CSRF token: {response.status_code}")
            return
        
        csrf_token = extract_csrf_token(response.text)
        if not csrf_token:
            return
        
        # List of API endpoints to test
        endpoints = [
            ('/api/users', 'POST', {'username': 'testuser', 'password': 'testpass'}),
            ('/api/scripts', 'POST', {'name': 'testscript', 'description': 'Test script'}),
            ('/api/settings', 'POST', {'key': 'test_setting', 'value': 'test_value'}),
            ('/api/change_password', 'POST', {'current_password': 'oldpass', 'new_password': 'newpass'})
        ]
        
        for endpoint, method, data in endpoints:
            # Try without CSRF token
            no_csrf_response = session.post(
                urljoin(base_url, endpoint),
                json=data
            )
            print(f"API {endpoint} without CSRF token: Status {no_csrf_response.status_code}")
            
            # Try with valid CSRF token and Referer header
            with_csrf_response = session.post(
                urljoin(base_url, endpoint),
                json=data,
                headers={
                    'X-CSRFToken': csrf_token,
                    'Referer': base_url,
                    'Origin': base_url
                }
            )
            print(f"API {endpoint} with valid CSRF token: Status {with_csrf_response.status_code}")
            print("-" * 40)
    except Exception as e:
        print(f"Error testing multiple API endpoints: {e}")

def test_token_longevity():
    """Test if CSRF token remains valid for reasonable time."""
    try:
        # Get a CSRF token
        response = session.get(urljoin(base_url, '/login'))
        csrf_token = extract_csrf_token(response.text)
        if not csrf_token:
            return
        
        print(f"Testing token longevity - Initial token: {csrf_token[:15]}...")
        
        # Wait for 30 seconds
        print("Waiting 30 seconds to test token validity...")
        time.sleep(30)
        
        # Try using the token after waiting with proper Referer header
        response = session.post(
            urljoin(base_url, '/login'),
            data={
                'username': 'admin',
                'password': 'password',
                'csrf_token': csrf_token
            },
            headers={
                'Referer': urljoin(base_url, '/login')
            }
        )
        print(f"Login with 30-second old token: Status code {response.status_code}")
        
        # Token should still be valid (not 400)
        if response.status_code != 400:
            print("✅ CSRF token is still valid after 30 seconds - good!")
        else:
            print("❌ CSRF token expired too quickly (less than 30 seconds)")
        
    except Exception as e:
        print(f"Error testing token longevity: {e}")

def run_all_tests():
    """Run all CSRF tests."""
    print("=" * 50)
    print("CSRF PROTECTION TEST SUITE")
    print("=" * 50)
    
    print("\n1. Testing login form without CSRF token:")
    test_login_without_csrf()
    
    print("\n2. Testing login form with invalid CSRF token:")
    test_login_with_invalid_csrf()
    
    print("\n3. Testing API endpoint without CSRF token:")
    test_api_without_csrf()
    
    print("\n4. Testing login with valid CSRF token:")
    test_login_with_valid_csrf()
    
    print("\n5. Testing multiple API endpoints:")
    test_multiple_api_endpoints()
    
    print("\n6. Testing CSRF token longevity:")
    test_token_longevity()
    
    print("\n" + "=" * 50)
    print("Test suite completed")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()