import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.aws_service import aws_service
from app.models.aws_profile_orm import AWSProfileORM
from tests.utils import create_aws_profile

def test_get_aws_profiles(app, auth_client):
    """Test get_aws_profiles endpoint"""
    with app.app_context():
        # Create test profiles
        profile1 = create_aws_profile(name='Profile 1')
        profile2 = create_aws_profile(name='Profile 2')
        
        # Make request to get all profiles
        response = auth_client.get('/api/aws_profiles')
        
        # Check response
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert len(data['profiles']) >= 2
        
        # Check if test profiles are in the response
        profile_names = [profile.get('name') for profile in data['profiles']]
        assert 'Profile 1' in profile_names
        assert 'Profile 2' in profile_names

def test_add_aws_profile(app, auth_client):
    """Test add_aws_profile endpoint"""
    with app.app_context():
        # Prepare request data
        profile_data = {
            'name': 'New Profile',
            'aws_access_key': 'FAKE_AWS_KEY',
            'aws_secret_key': 'FAKE_AWS_SECRET',
            'aws_region': 'us-west-2',
            'is_default': False
        }
        
        # Mock the AWS validation method
        with patch.object(aws_service, '_validate_aws_credentials') as mock_validate, \
             patch.object(aws_service, 'create_profile', wraps=aws_service.create_profile) as mock_create:
            # Configure mock to return True (valid credentials)
            mock_validate.return_value = True
            
            # Make request to add a profile
            response = auth_client.post('/api/aws_profiles', json=profile_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'profile_id' in data
            
            # Verify create_profile was called with correct arguments
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['name'] == 'New Profile'
            assert call_args['aws_access_key'] == 'FAKE_AWS_KEY'
            assert call_args['aws_secret_key'] == 'FAKE_AWS_SECRET'
            assert call_args['aws_region'] == 'us-west-2'
            assert call_args['is_default'] is False

def test_add_aws_profile_missing_data(app, auth_client):
    """Test add_aws_profile endpoint with missing required data"""
    with app.app_context():
        # Prepare incomplete data (missing aws_access_key)
        incomplete_data = {
            'name': 'New Profile',
            'aws_secret_key': 'FAKE_AWS_SECRET',
            'aws_region': 'us-west-2'
            # Missing 'aws_access_key' which is required
        }
        
        # Make request with incomplete data
        response = auth_client.post('/api/aws_profiles', json=incomplete_data)
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_add_aws_profile_invalid_credentials(app, auth_client):
    """Test add_aws_profile endpoint with invalid AWS credentials"""
    with app.app_context():
        # Prepare request data
        profile_data = {
            'name': 'New Profile',
            'aws_access_key': 'FAKE_AWS_KEY',
            'aws_secret_key': 'FAKE_AWS_SECRET',
            'aws_region': 'us-west-2',
            'is_default': False
        }
        
        # Mock the AWS validation method to raise an exception
        with patch.object(aws_service, '_validate_aws_credentials') as mock_validate:
            # Configure mock to raise exception (invalid credentials)
            mock_validate.side_effect = Exception("Invalid AWS credentials")
            
            # Make request with invalid credentials
            response = auth_client.post('/api/aws_profiles', json=profile_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'invalid aws credentials' in data['message'].lower()

def test_add_aws_profile_duplicate_name(app, auth_client):
    """Test add_aws_profile endpoint with duplicate profile name"""
    with app.app_context():
        # Create a profile first
        existing_profile = create_aws_profile(name='Existing Profile')
        
        # Prepare request data with same name
        profile_data = {
            'name': 'Existing Profile',  # Same name as existing profile
            'aws_access_key': 'FAKE_AWS_KEY',
            'aws_secret_key': 'FAKE_AWS_SECRET',
            'aws_region': 'us-west-2',
            'is_default': False
        }
        
        # Mock the AWS validation method
        with patch.object(aws_service, '_validate_aws_credentials') as mock_validate:
            # Configure mock to return True (valid credentials)
            mock_validate.return_value = True
            
            # Make request with duplicate name
            response = auth_client.post('/api/aws_profiles', json=profile_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'already exists' in data['message'].lower()

def test_get_aws_profile_by_id(app, auth_client):
    """Test get_aws_profile endpoint"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Test Profile')
        
        # Make request to get profile by ID
        response = auth_client.get(f'/api/aws_profiles/{profile.id}')
        
        # Check response
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['profile']['id'] == profile.id
        assert data['profile']['name'] == 'Test Profile'
        assert data['profile']['aws_region'] == 'us-east-1'  # Default from create_aws_profile

def test_get_aws_profile_not_found(app, auth_client):
    """Test get_aws_profile endpoint with non-existent ID"""
    with app.app_context():
        # Make request with non-existent profile ID
        response = auth_client.get('/api/aws_profiles/999')
        
        # Check response
        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

def test_update_aws_profile(app, auth_client):
    """Test update_aws_profile endpoint"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Profile to Update')
        
        # Prepare update data
        update_data = {
            'name': 'Updated Profile',
            'aws_region': 'eu-west-1'
            # Not updating keys
        }
        
        # Mock the AWS validation method
        with patch.object(aws_service, '_validate_aws_credentials') as mock_validate, \
             patch.object(aws_service, 'update_profile', wraps=aws_service.update_profile) as mock_update:
            # Configure mock to return True (valid credentials)
            mock_validate.return_value = True
            
            # Make request to update profile
            response = auth_client.put(f'/api/aws_profiles/{profile.id}', json=update_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify update_profile was called with correct arguments
            mock_update.assert_called_once()
            call_args = mock_update.call_args[1]
            assert call_args['profile_id'] == profile.id
            assert call_args['name'] == 'Updated Profile'
            assert call_args['aws_region'] == 'eu-west-1'
            # Other parameters should be None, so they'll use existing values

def test_update_aws_profile_empty_data(app, auth_client):
    """Test update_aws_profile endpoint with empty data"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Profile to Update')
        
        # Make request with empty data
        response = auth_client.put(f'/api/aws_profiles/{profile.id}', json={})
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'no data provided' in data['message'].lower()

def test_update_aws_profile_not_found(app, auth_client):
    """Test update_aws_profile endpoint with non-existent ID"""
    with app.app_context():
        # Prepare update data
        update_data = {
            'name': 'Updated Profile'
        }
        
        # Mock the update_profile method to raise ValueError
        with patch.object(aws_service, 'update_profile') as mock_update:
            # Configure mock to raise ValueError (profile not found)
            mock_update.side_effect = ValueError("Profile not found")
            
            # Make request with non-existent profile ID
            response = auth_client.put('/api/aws_profiles/999', json=update_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_update_aws_profile_invalid_credentials(app, auth_client):
    """Test update_aws_profile endpoint with invalid AWS credentials"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Profile to Update')
        
        # Prepare update data with new credentials
        update_data = {
            'aws_access_key': 'FAKE_AWS_KEY',
            'aws_secret_key': 'FAKE_AWS_SECRET'
        }
        
        # Mock the AWS validation method to raise an exception
        with patch.object(aws_service, '_validate_aws_credentials') as mock_validate:
            # Configure mock to raise exception (invalid credentials)
            mock_validate.side_effect = Exception("Invalid AWS credentials")
            
            # Make request with invalid credentials
            response = auth_client.put(f'/api/aws_profiles/{profile.id}', json=update_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'invalid aws credentials' in data['message'].lower()

def test_delete_aws_profile(app, auth_client):
    """Test delete_aws_profile endpoint"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Profile to Delete')
        
        # Mock the delete_profile method
        with patch.object(aws_service, 'delete_profile') as mock_delete:
            # Configure mock to return True (success)
            mock_delete.return_value = True
            
            # Make request to delete profile
            response = auth_client.delete(f'/api/aws_profiles/{profile.id}')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify delete_profile was called with correct ID
            mock_delete.assert_called_once_with(profile.id)

def test_delete_aws_profile_not_found(app, auth_client):
    """Test delete_aws_profile endpoint with non-existent ID"""
    with app.app_context():
        # Mock the delete_profile method to raise ValueError
        with patch.object(aws_service, 'delete_profile') as mock_delete:
            # Configure mock to raise ValueError (profile not found)
            mock_delete.side_effect = ValueError("Profile not found")
            
            # Make request with non-existent profile ID
            response = auth_client.delete('/api/aws_profiles/999')
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_delete_aws_profile_in_use(app, auth_client):
    """Test delete_aws_profile endpoint with profile in use"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='Profile in Use')
        
        # Mock the delete_profile method to raise ValueError (profile in use)
        with patch.object(aws_service, 'delete_profile') as mock_delete:
            # Configure mock to raise ValueError (profile in use)
            mock_delete.side_effect = ValueError("This profile is in use by execution history entries and cannot be deleted")
            
            # Make request to delete profile in use
            response = auth_client.delete(f'/api/aws_profiles/{profile.id}')
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'in use' in data['message'].lower()

def test_set_default_profile(app, auth_client):
    """Test set_default_aws_profile endpoint"""
    with app.app_context():
        # Create a test profile
        profile = create_aws_profile(name='New Default Profile')
        
        # Mock the set_default_profile method
        with patch.object(aws_service, 'set_default_profile') as mock_set_default:
            # Configure mock to return True (success)
            mock_set_default.return_value = True
            
            # Make request to set profile as default
            response = auth_client.post(f'/api/aws_profiles/{profile.id}/set_default')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify set_default_profile was called with correct ID
            mock_set_default.assert_called_once_with(profile.id)

def test_set_default_profile_not_found(app, auth_client):
    """Test set_default_aws_profile endpoint with non-existent ID"""
    with app.app_context():
        # Mock the set_default_profile method to raise ValueError
        with patch.object(aws_service, 'set_default_profile') as mock_set_default:
            # Configure mock to raise ValueError (profile not found)
            mock_set_default.side_effect = ValueError("Profile not found")
            
            # Make request with non-existent profile ID
            response = auth_client.post('/api/aws_profiles/999/set_default')
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()