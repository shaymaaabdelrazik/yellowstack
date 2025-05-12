import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.scheduler_service import scheduler_service
from tests.utils import create_user, create_script, create_aws_profile

def test_get_schedules(app, auth_client):
    """Test get_schedules endpoint"""
    with app.app_context():
        # Mock the get_schedules method
        with patch.object(scheduler_service, 'get_schedules') as mock_get_schedules:
            # Prepare mock data
            mock_schedules = [
                {
                    'id': 1,
                    'script_id': 1,
                    'script_name': 'Test Script 1',
                    'profile_id': 1,
                    'profile_name': 'Test Profile',
                    'user_id': 1,
                    'username': 'testuser',
                    'schedule_type': 'daily',
                    'schedule_value': '12:00',
                    'enabled': 1,
                    'next_run': (datetime.now() + timedelta(days=1)).isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'script_id': 2,
                    'script_name': 'Test Script 2',
                    'profile_id': 1,
                    'profile_name': 'Test Profile',
                    'user_id': 1,
                    'username': 'testuser',
                    'schedule_type': 'interval',
                    'schedule_value': '6',
                    'enabled': 1,
                    'next_run': (datetime.now() + timedelta(hours=6)).isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            ]
            
            # Configure mock to return test data
            mock_get_schedules.return_value = mock_schedules
            
            # Make request to get all schedules
            response = auth_client.get('/api/schedules')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert len(data['schedules']) == 2
            assert data['schedules'][0]['id'] == 1
            assert data['schedules'][1]['id'] == 2
            
            # Verify get_schedules was called with default parameters
            mock_get_schedules.assert_called_once_with(False)

def test_get_schedules_include_disabled(app, auth_client):
    """Test get_schedules endpoint with include_disabled=true"""
    with app.app_context():
        # Mock the get_schedules method
        with patch.object(scheduler_service, 'get_schedules') as mock_get_schedules:
            # Configure mock to return empty list
            mock_get_schedules.return_value = []
            
            # Make request with include_disabled parameter
            response = auth_client.get('/api/schedules?include_disabled=true')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert len(data['schedules']) == 0
            
            # Verify get_schedules was called with include_disabled=True
            mock_get_schedules.assert_called_once_with(True)

def test_get_schedule_by_id(app, auth_client):
    """Test get_schedule_by_id endpoint"""
    with app.app_context():
        # Mock the get_schedule method
        with patch.object(scheduler_service, 'get_schedule') as mock_get_schedule:
            # Prepare mock data
            mock_schedule = {
                'id': 1,
                'script_id': 1,
                'script_name': 'Test Script',
                'profile_id': 1,
                'profile_name': 'Test Profile',
                'user_id': 1,
                'username': 'testuser',
                'schedule_type': 'daily',
                'schedule_value': '12:00',
                'enabled': 1,
                'next_run': (datetime.now() + timedelta(days=1)).isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'parameters': json.dumps([{'name': 'param1', 'value': 'value1'}])
            }
            
            # Configure mock to return test data
            mock_get_schedule.return_value = mock_schedule
            
            # Make request to get schedule by ID
            response = auth_client.get('/api/schedules/1')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['schedule']['id'] == 1
            assert data['schedule']['script_name'] == 'Test Script'
            
            # Verify get_schedule was called with correct ID
            mock_get_schedule.assert_called_once_with(1)

def test_get_schedule_not_found(app, auth_client):
    """Test get_schedule_by_id endpoint with non-existent ID"""
    with app.app_context():
        # Mock the get_schedule method
        with patch.object(scheduler_service, 'get_schedule') as mock_get_schedule:
            # Configure mock to return None (schedule not found)
            mock_get_schedule.return_value = None
            
            # Make request with non-existent schedule ID
            response = auth_client.get('/api/schedules/999')
            
            # Check response
            assert response.status_code == 404
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_create_schedule(app, auth_client):
    """Test create_schedule endpoint"""
    with app.app_context():
        # Prepare request data
        schedule_data = {
            'script_id': 1,
            'profile_id': 1,
            'schedule_type': 'daily',
            'schedule_value': '12:00',
            'parameters': json.dumps([{'name': 'param1', 'value': 'value1'}])
        }
        
        # Mock the create_schedule method
        with patch.object(scheduler_service, 'create_schedule') as mock_create_schedule:
            # Prepare mock response
            mock_result = {
                'success': True,
                'id': 123,
                'job_id': 'job_123',
                'next_run': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            # Configure mock to return success
            mock_create_schedule.return_value = mock_result
            
            # Make request to create schedule
            response = auth_client.post('/api/schedules', json=schedule_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['id'] == 123
            assert data['job_id'] == 'job_123'
            assert 'next_run' in data
            
            # Verify create_schedule was called with correct arguments
            mock_create_schedule.assert_called_once_with(
                script_id=1,
                profile_id=1,
                user_id=1,  # from auth_client
                schedule_type='daily',
                schedule_value='12:00',
                parameters=schedule_data['parameters']  # The API passes this directly
            )

def test_create_schedule_missing_data(app, auth_client):
    """Test create_schedule endpoint with missing required data"""
    with app.app_context():
        # Prepare incomplete data (missing profile_id)
        incomplete_data = {
            'script_id': 1,
            'schedule_type': 'daily',
            'schedule_value': '12:00'
            # Missing 'profile_id' which is required
        }
        
        # Make request with incomplete data
        response = auth_client.post('/api/schedules', json=incomplete_data)
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_create_schedule_invalid_type(app, auth_client):
    """Test create_schedule endpoint with invalid schedule type"""
    with app.app_context():
        # Prepare data with invalid schedule type
        invalid_data = {
            'script_id': 1,
            'profile_id': 1,
            'schedule_type': 'invalid',  # Invalid type
            'schedule_value': '12:00'
        }
        
        # Mock the create_schedule method to raise ValueError
        with patch.object(scheduler_service, 'create_schedule') as mock_create_schedule:
            # Configure mock to raise ValueError for invalid type
            mock_create_schedule.side_effect = ValueError("Invalid schedule type")
            
            # Make request with invalid data
            response = auth_client.post('/api/schedules', json=invalid_data)
            
            # Check response (API returns 500 for exceptions)
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'error creating schedule' in data['message'].lower()

def test_update_schedule(app, auth_client):
    """Test update_schedule endpoint"""
    with app.app_context():
        # Prepare update data
        update_data = {
            'enabled': False,
            'schedule_type': 'interval',
            'schedule_value': '8',
            'profile_id': 2,
            'parameters': json.dumps([{'name': 'updated_param', 'value': 'updated_value'}])
        }
        
        # Mock the update_schedule method
        with patch.object(scheduler_service, 'update_schedule') as mock_update_schedule:
            # Prepare mock response
            mock_result = {
                'success': True,
                'next_run': (datetime.now() + timedelta(hours=8)).isoformat()
            }
            
            # Configure mock to return success
            mock_update_schedule.return_value = mock_result
            
            # Make request to update schedule
            response = auth_client.put('/api/schedules/1', json=update_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'next_run' in data
            
            # Verify update_schedule was called with correct arguments
            mock_update_schedule.assert_called_once_with(
                schedule_id=1,
                enabled=False,
                schedule_type='interval',
                schedule_value='8',
                profile_id=2,
                parameters=update_data['parameters']  # The API passes this directly
            )

def test_update_schedule_empty_data(app, auth_client):
    """Test update_schedule endpoint with empty data"""
    with app.app_context():
        # Make request with empty data
        response = auth_client.put('/api/schedules/1', json={})
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'no data provided' in data['message'].lower()

def test_update_schedule_invalid_value(app, auth_client):
    """Test update_schedule endpoint with invalid schedule value"""
    with app.app_context():
        # Prepare data with invalid schedule value
        invalid_data = {
            'schedule_type': 'daily',
            'schedule_value': '25:00'  # Invalid time
        }
        
        # Mock the update_schedule method to raise ValueError
        with patch.object(scheduler_service, 'update_schedule') as mock_update_schedule:
            # Configure mock to raise ValueError for invalid value
            mock_update_schedule.side_effect = ValueError("Invalid schedule value")
            
            # Make request with invalid data
            response = auth_client.put('/api/schedules/1', json=invalid_data)
            
            # Check response (API returns 500 for exceptions)
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'internal server error' in data['message'].lower()

def test_update_schedule_not_found(app, auth_client):
    """Test update_schedule endpoint with non-existent ID"""
    with app.app_context():
        # Prepare update data
        update_data = {
            'enabled': False
        }
        
        # Mock the update_schedule method to raise ValueError for not found
        with patch.object(scheduler_service, 'update_schedule') as mock_update_schedule:
            # Configure mock to raise ValueError (schedule not found)
            mock_update_schedule.side_effect = ValueError("Schedule not found")
            
            # Make request with non-existent schedule ID
            response = auth_client.put('/api/schedules/999', json=update_data)
            
            # Check response (API returns 500 for exceptions)
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'internal server error' in data['message'].lower()

def test_delete_schedule(app, auth_client):
    """Test delete_schedule endpoint"""
    with app.app_context():
        # Mock the delete_schedule method
        with patch.object(scheduler_service, 'delete_schedule') as mock_delete_schedule:
            # Configure mock to return success
            mock_delete_schedule.return_value = {'success': True}
            
            # Make request to delete schedule
            response = auth_client.delete('/api/schedules/1')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify delete_schedule was called with correct ID
            mock_delete_schedule.assert_called_once_with(1)

def test_delete_schedule_not_found(app, auth_client):
    """Test delete_schedule endpoint with non-existent ID"""
    with app.app_context():
        # Mock the delete_schedule method to raise ValueError
        with patch.object(scheduler_service, 'delete_schedule') as mock_delete_schedule:
            # Configure mock to raise ValueError (schedule not found)
            mock_delete_schedule.side_effect = ValueError("Schedule not found")
            
            # Make request with non-existent schedule ID
            response = auth_client.delete('/api/schedules/999')
            
            # Check response (API returns 500 for exceptions)
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'internal server error' in data['message'].lower()

def test_manual_run(app, auth_client):
    """Test manual_run endpoint"""
    with app.app_context():
        # Mock the manual_run method
        with patch.object(scheduler_service, 'manual_run') as mock_manual_run:
            # Prepare mock response
            mock_result = {
                'success': True,
                'execution_id': 123
            }
            
            # Configure mock to return success
            mock_manual_run.return_value = mock_result
            
            # Make request to manually run schedule
            response = auth_client.post('/api/schedules/1/run')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['execution_id'] == 123
            
            # Verify manual_run was called with correct ID
            mock_manual_run.assert_called_once_with(1)

def test_manual_run_not_found(app, auth_client):
    """Test manual_run endpoint with non-existent ID"""
    with app.app_context():
        # Mock the manual_run method to raise ValueError
        with patch.object(scheduler_service, 'manual_run') as mock_manual_run:
            # Configure mock to raise ValueError (schedule not found)
            mock_manual_run.side_effect = ValueError("Schedule not found")
            
            # Make request with non-existent schedule ID
            response = auth_client.post('/api/schedules/999/run')
            
            # Check response (API returns 500 for exceptions)
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'internal server error' in data['message'].lower()