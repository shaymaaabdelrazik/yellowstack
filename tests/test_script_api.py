import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.script_service import script_service
from tests.utils import create_script, create_user

def test_get_scripts(app, auth_client):
    """Test get_scripts endpoint"""
    with app.app_context():
        # Create some test scripts
        script1 = create_script(name='Script 1', path='/path/to/script1.py')
        script2 = create_script(name='Script 2', path='/path/to/script2.py')
        
        # Make request to get all scripts
        response = auth_client.get('/api/scripts')
        
        # Check response
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert len(data['scripts']) >= 2
        
        # Check if test scripts are in the response
        script_names = [script.get('name') for script in data['scripts']]
        assert 'Script 1' in script_names
        assert 'Script 2' in script_names

def test_get_scripts_empty(app, auth_client):
    """Test get_scripts endpoint when no scripts exist"""
    with app.app_context():
        # Mock the get_all_scripts method to return empty list
        with patch.object(script_service, 'get_all_scripts') as mock_get_all:
            mock_get_all.return_value = []
            
            # Make request to get all scripts
            response = auth_client.get('/api/scripts')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert len(data['scripts']) == 0

def test_add_script(app, auth_client):
    """Test add_script endpoint"""
    with app.app_context():
        # Prepare data for new script
        script_data = {
            'name': 'New Script',
            'path': '/path/to/new_script.py',
            'description': 'A new test script',
            'parameters': json.dumps([{'name': 'param1', 'default': 'value1'}])
        }
        
        # Mock the create_script method
        with patch.object(script_service, 'create_script') as mock_create_script:
            # Configure mock to return success
            mock_create_script.return_value = 123  # script_id
            
            # Make request to add script
            response = auth_client.post('/api/scripts', json=script_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['script_id'] == 123
            
            # Verify create_script was called with correct arguments
            mock_create_script.assert_called_once_with(
                name='New Script', 
                description='A new test script', 
                path='/path/to/new_script.py',
                parameters=json.dumps([{'name': 'param1', 'default': 'value1'}]),
                user_id=1  # user_id from auth_client
            )

def test_add_script_missing_data(app, auth_client):
    """Test add_script endpoint with missing required data"""
    with app.app_context():
        # Prepare incomplete data (missing path)
        incomplete_data = {
            'name': 'New Script',
            'description': 'A new test script'
            # Missing 'path' which is required
        }
        
        # Make request with incomplete data
        response = auth_client.post('/api/scripts', json=incomplete_data)
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_add_script_invalid_path(app, auth_client):
    """Test add_script endpoint with invalid script path"""
    with app.app_context():
        # Prepare data with invalid path
        script_data = {
            'name': 'Invalid Script',
            'path': '/path/to/nonexistent_script.py',
            'description': 'A script with invalid path'
        }
        
        # Mock the create_script method to raise ValueError
        with patch.object(script_service, 'create_script') as mock_create_script:
            # Configure mock to raise ValueError (invalid path)
            mock_create_script.side_effect = ValueError("Script file does not exist")
            
            # Make request to add script
            response = auth_client.post('/api/scripts', json=script_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'does not exist' in data['message']

def test_get_script_by_id(app, auth_client):
    """Test get_script_by_id endpoint"""
    with app.app_context():
        # Create a test script
        script = create_script(name='Test Script', path='/path/to/test_script.py')
        
        # Make request to get script by ID
        response = auth_client.get(f'/api/scripts/{script.id}')
        
        # Check response
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['script']['id'] == script.id
        assert data['script']['name'] == 'Test Script'
        assert data['script']['path'] == '/path/to/test_script.py'

def test_get_script_not_found(app, auth_client):
    """Test get_script_by_id endpoint with non-existent ID"""
    with app.app_context():
        # Mock the get_script_by_id method
        with patch.object(script_service, 'get_script_by_id') as mock_get_script:
            # Configure mock to return None (script not found)
            mock_get_script.return_value = None
            
            # Make request with non-existent script ID
            response = auth_client.get('/api/scripts/999')
            
            # Check response
            assert response.status_code == 404
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_update_script(app, auth_client):
    """Test update_script endpoint"""
    with app.app_context():
        # Create a test script
        script = create_script(name='Original Script', path='/path/to/original.py')
        
        # Prepare update data
        update_data = {
            'name': 'Updated Script',
            'description': 'Updated description',
            'path': '/path/to/updated.py',
            'parameters': json.dumps([{'name': 'updated_param', 'default': 'updated_value'}])
        }
        
        # Mock the update_script method
        with patch.object(script_service, 'update_script') as mock_update_script:
            # Configure mock to return success
            mock_update_script.return_value = True
            
            # Make request to update script
            response = auth_client.put(f'/api/scripts/{script.id}', json=update_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify update_script was called with correct arguments
            mock_update_script.assert_called_once_with(
                script_id=script.id,
                name='Updated Script',
                description='Updated description',
                path='/path/to/updated.py',
                parameters=json.dumps([{'name': 'updated_param', 'default': 'updated_value'}])
            )

def test_update_script_not_found(app, auth_client):
    """Test update_script endpoint with non-existent ID"""
    with app.app_context():
        # Prepare update data
        update_data = {
            'name': 'Updated Script',
            'description': 'Updated description'
        }
        
        # Mock the update_script method
        with patch.object(script_service, 'update_script') as mock_update_script:
            # Configure mock to return False (script not found)
            mock_update_script.return_value = False
            
            # Make request with non-existent script ID
            response = auth_client.put('/api/scripts/999', json=update_data)
            
            # Unlike get_script, update_script just returns success: True
            # even when the script isn't found
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True

def test_update_script_invalid_path(app, auth_client):
    """Test update_script endpoint with invalid script path"""
    with app.app_context():
        # Create a test script
        script = create_script()
        
        # Prepare update data with invalid path
        update_data = {
            'path': '/path/to/nonexistent.py'
        }
        
        # Mock the update_script method to raise ValueError
        with patch.object(script_service, 'update_script') as mock_update_script:
            # Configure mock to raise ValueError (invalid path)
            mock_update_script.side_effect = ValueError("Script file does not exist")
            
            # Make request to update script
            response = auth_client.put(f'/api/scripts/{script.id}', json=update_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'does not exist' in data['message']

def test_delete_script(app, auth_client):
    """Test delete_script endpoint"""
    with app.app_context():
        # Create a test script
        script = create_script(name='Script to Delete')
        
        # Mock the delete_script method
        with patch.object(script_service, 'delete_script') as mock_delete_script:
            # Configure mock to return success
            mock_delete_script.return_value = True
            
            # Make request to delete script
            response = auth_client.delete(f'/api/scripts/{script.id}')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify delete_script was called with correct argument
            mock_delete_script.assert_called_once_with(script.id)

def test_delete_script_not_found(app, auth_client):
    """Test delete_script endpoint with non-existent ID"""
    with app.app_context():
        # Mock the delete_script method
        with patch.object(script_service, 'delete_script') as mock_delete_script:
            # Configure mock to return False (script not found)
            mock_delete_script.return_value = False
            
            # Make request with non-existent script ID
            response = auth_client.delete('/api/scripts/999')
            
            # Check response - unlike get_script, delete just returns success
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True

def test_delete_script_with_error(app, auth_client):
    """Test delete_script endpoint when an error occurs"""
    with app.app_context():
        # Create a test script
        script = create_script()
        
        # Mock the delete_script method to raise an exception
        with patch.object(script_service, 'delete_script') as mock_delete_script:
            # Configure mock to raise an exception
            mock_delete_script.side_effect = Exception("Database error")
            
            # Make request to delete script
            response = auth_client.delete(f'/api/scripts/{script.id}')
            
            # Check response (according to the API implementation, general exceptions return 400)
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'Database error' in data['message']