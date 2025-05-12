import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.execution_service import execution_service
from tests.utils import create_user, create_script

def test_get_recent_executions(app, auth_client):
    """Test get_recent_executions endpoint"""
    with app.app_context():
        # Mock the get_recent_executions method
        with patch.object(execution_service, 'get_recent_executions') as mock_get_recent:
            # Prepare mock data
            mock_executions = [
                {
                    'id': 1,
                    'script_name': 'Test Script 1',
                    'status': 'COMPLETED',
                    'start_time': '2023-10-01 10:00:00',
                    'end_time': '2023-10-01 10:01:00',
                    'user_name': 'testuser'
                },
                {
                    'id': 2,
                    'script_name': 'Test Script 2',
                    'status': 'FAILED',
                    'start_time': '2023-10-01 11:00:00',
                    'end_time': '2023-10-01 11:02:00',
                    'user_name': 'testuser'
                }
            ]
            
            # Configure mock to return test data
            mock_get_recent.return_value = mock_executions
            
            # Make request to get recent executions
            response = auth_client.get('/api/recent_executions')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert len(data['executions']) == 2
            assert data['executions'][0]['id'] == 1
            assert data['executions'][1]['id'] == 2
            
            # Verify get_recent_executions was called
            mock_get_recent.assert_called_once()

def test_get_execution_details(app, auth_client):
    """Test get_execution_details endpoint"""
    with app.app_context():
        # Mock the get_execution_by_id method
        with patch.object(execution_service, 'get_execution_by_id') as mock_get_execution:
            # Prepare mock data
            mock_execution = {
                'id': 1,
                'script_name': 'Test Script',
                'status': 'COMPLETED',
                'start_time': '2023-10-01 10:00:00',
                'end_time': '2023-10-01 10:01:00',
                'output': 'Script output',
                'error': None,
                'aws_profile': 'Test Profile',
                'parameters': json.dumps([{'name': 'param1', 'value': 'value1'}]),
                'user_name': 'testuser'
            }
            
            # Configure mock to return test data
            mock_get_execution.return_value = mock_execution
            
            # Make request to get execution details
            response = auth_client.get('/api/execution_details/1')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['execution']['id'] == 1
            assert data['execution']['script_name'] == 'Test Script'
            
            # Verify get_execution_by_id was called with correct arguments
            mock_get_execution.assert_called_once_with(1)

def test_get_execution_details_not_found(app, auth_client):
    """Test get_execution_details endpoint with non-existent ID"""
    with app.app_context():
        # Mock the get_execution_by_id method
        with patch.object(execution_service, 'get_execution_by_id') as mock_get_execution:
            # Configure mock to return None (execution not found)
            mock_get_execution.return_value = None
            
            # Make request with non-existent execution ID
            response = auth_client.get('/api/execution_details/999')
            
            # Check response
            assert response.status_code == 404
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_run_script(app, auth_client):
    """Test run_script endpoint"""
    with app.app_context():
        # Prepare request data
        execution_data = {
            'script_id': 1,
            'profile_id': 1,
            'parameters': json.dumps([{'name': 'param1', 'value': 'value1'}]),
            'region_override': 'us-west-2'
        }
        
        # Mock the run_script method
        with patch.object(execution_service, 'run_script') as mock_run_script:
            # Configure mock to return success
            mock_run_script.return_value = 123  # execution_id
            
            # Make request to run script
            response = auth_client.post('/api/run_script', json=execution_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['execution_id'] == 123
            
            # Verify run_script was called with correct arguments
            mock_run_script.assert_called_once_with(
                script_id=1,
                profile_id=1,
                user_id=1,  # From auth_client
                parameters=[{'name': 'param1', 'value': 'value1'}],  # JSON is automatically loaded
                region_override='us-west-2'
            )

def test_run_script_missing_data(app, auth_client):
    """Test run_script endpoint with missing required data"""
    with app.app_context():
        # Prepare incomplete data (missing profile_id)
        incomplete_data = {
            'script_id': 1
            # Missing 'profile_id' which is required
        }
        
        # Make request with incomplete data
        response = auth_client.post('/api/run_script', json=incomplete_data)
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_run_script_with_error(app, auth_client):
    """Test run_script endpoint when error occurs"""
    with app.app_context():
        # Prepare request data
        execution_data = {
            'script_id': 1,
            'profile_id': 1
        }
        
        # Mock the run_script method to raise an exception
        with patch.object(execution_service, 'run_script') as mock_run_script:
            # Configure mock to raise an exception
            mock_run_script.side_effect = Exception("Failed to run script")
            
            # Make request to run script
            response = auth_client.post('/api/run_script', json=execution_data)
            
            # Check response
            assert response.status_code == 500
            data = response.json
            assert data['success'] is False
            assert 'internal server error' in data['message'].lower()

def test_get_execution_history(app, auth_client):
    """Test get_execution_history endpoint"""
    with app.app_context():
        # Mock the get_execution_history method
        with patch.object(execution_service, 'get_execution_history') as mock_get_history:
            # Prepare mock data
            mock_history = {
                'executions': [
                    {
                        'id': 1,
                        'script_name': 'Test Script 1',
                        'status': 'COMPLETED',
                        'start_time': '2023-10-01 10:00:00'
                    },
                    {
                        'id': 2,
                        'script_name': 'Test Script 2',
                        'status': 'FAILED',
                        'start_time': '2023-10-01 11:00:00'
                    }
                ],
                'current_page': 1,
                'total_pages': 1,
                'total_count': 2
            }
            
            # Configure mock to return test data
            mock_get_history.return_value = mock_history
            
            # Make request to get execution history
            response = auth_client.get('/api/execution_history')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert len(data['executions']) == 2
            assert data['current_page'] == 1
            assert data['total_pages'] == 1
            
            # Verify get_execution_history was called with default parameters
            mock_get_history.assert_called_once_with(1, filters={})

def test_get_execution_history_with_filters(app, auth_client):
    """Test get_execution_history endpoint with filters"""
    with app.app_context():
        # Mock the get_execution_history method
        with patch.object(execution_service, 'get_execution_history') as mock_get_history:
            # Configure mock to return empty result
            mock_get_history.return_value = {
                'executions': [],
                'current_page': 1,
                'total_pages': 0,
                'total_count': 0
            }
            
            # Make request with filters
            response = auth_client.get('/api/execution_history?page=2&script_id=1&status=FAILED&date=2023-10-01')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify get_execution_history was called with correct parameters
            expected_filters = {
                'script_id': 1,  # This is converted to int
                'status': 'FAILED',
                'date': '2023-10-01'
            }
            mock_get_history.assert_called_once_with(2, filters=expected_filters)

def test_get_execution_stats(app, auth_client):
    """Test get_execution_stats endpoint"""
    with app.app_context():
        # Mock the get_execution_stats method
        with patch.object(execution_service, 'get_execution_stats') as mock_get_stats:
            # Prepare mock data
            mock_stats = {
                'status_data': [10, 5, 2],
                'time_data': {
                    'labels': ['Day 1', 'Day 2', 'Day 3'],
                    'datasets': [
                        {'label': 'Completed', 'data': [3, 4, 3]},
                        {'label': 'Failed', 'data': [1, 2, 2]}
                    ]
                }
            }
            
            # Configure mock to return test data
            mock_get_stats.return_value = mock_stats
            
            # Make request to get execution stats
            response = auth_client.get('/api/execution_stats')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'data' in data  # API returns the data under 'data' key
            
            # Verify get_execution_stats was called with default days parameter
            mock_get_stats.assert_called_once_with(7)

def test_get_execution_stats_custom_days(app, auth_client):
    """Test get_execution_stats endpoint with custom days parameter"""
    with app.app_context():
        # Mock the get_execution_stats method
        with patch.object(execution_service, 'get_execution_stats') as mock_get_stats:
            # Configure mock to return empty stats
            mock_get_stats.return_value = {'status_data': [], 'time_data': {}}
            
            # Make request with custom days parameter
            response = auth_client.get('/api/execution_stats?days=30')
            
            # Check response
            assert response.status_code == 200
            
            # Verify get_execution_stats was called with correct days parameter
            mock_get_stats.assert_called_once_with(30)  # API directly passes the integer

def test_get_ai_help(app, auth_client):
    """Test get_ai_help endpoint"""
    with app.app_context():
        # Mock the get_ai_help method
        with patch.object(execution_service, 'get_ai_help') as mock_get_ai_help:
            # Prepare mock data
            mock_ai_help = {
                'error': 'ImportError: No module named boto3',
                'ai_help': 'It looks like you are missing the boto3 module',
                'solution': 'Install boto3 using pip: pip install boto3'
            }
            
            # Configure mock to return test data
            mock_get_ai_help.return_value = mock_ai_help
            
            # Make request to get AI help
            response = auth_client.get('/api/ai_help/1')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert data['error'] == 'ImportError: No module named boto3'
            assert 'ai_help' in data
            assert 'solution' in data
            
            # Verify get_ai_help was called with correct execution_id
            mock_get_ai_help.assert_called_once_with(1)

def test_get_ai_help_not_found(app, auth_client):
    """Test get_ai_help endpoint with non-existent execution ID"""
    with app.app_context():
        # Mock the get_ai_help method to raise ValueError
        with patch.object(execution_service, 'get_ai_help') as mock_get_ai_help:
            # Configure mock to raise ValueError (execution not found)
            mock_get_ai_help.side_effect = ValueError("Execution not found")
            
            # Make request with non-existent execution ID
            response = auth_client.get('/api/ai_help/999')
            
            # Check response
            assert response.status_code == 404
            data = response.json
            assert data['success'] is False
            assert 'not found' in data['message'].lower()

def test_cancel_execution(app, auth_client):
    """Test cancel_execution endpoint"""
    with app.app_context():
        # Mock the cancel_execution method
        with patch.object(execution_service, 'cancel_execution') as mock_cancel:
            # Configure mock to return success
            mock_cancel.return_value = True
            
            # Make request to cancel execution
            response = auth_client.post('/api/cancel_execution/1')
            
            # Check response
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'cancelled' in data['message'].lower()
            
            # Verify cancel_execution was called with correct execution_id
            mock_cancel.assert_called_once_with(1)

def test_cancel_execution_not_found(app, auth_client):
    """Test cancel_execution endpoint with non-existent execution ID"""
    with app.app_context():
        # Mock the cancel_execution method to raise ValueError
        with patch.object(execution_service, 'cancel_execution') as mock_cancel:
            # Configure mock to raise ValueError (execution not found)
            mock_cancel.side_effect = ValueError("Execution cannot be cancelled or not found")
            
            # Make request with non-existent or non-running execution ID
            response = auth_client.post('/api/cancel_execution/999')
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'cannot be cancelled' in data['message'].lower()

def test_provide_input(app, auth_client):
    """Test provide_input endpoint"""
    with app.app_context():
        # Prepare request data
        input_data = {
            'input': 'test input'
        }
        
        # Mock the provide_input method
        with patch.object(execution_service, 'provide_input') as mock_provide_input:
            # Configure mock to return success
            mock_provide_input.return_value = True
            
            # Make request to provide input
            response = auth_client.post('/api/provide_input/1', json=input_data)
            
            # Check response - the API just returns success without a message
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            
            # Verify provide_input was called with correct arguments
            mock_provide_input.assert_called_once_with(1, 'test input')

def test_provide_input_missing_data(app, auth_client):
    """Test provide_input endpoint with missing required data"""
    with app.app_context():
        # Make request without input data
        response = auth_client.post('/api/provide_input/1', json={})
        
        # Check response
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'required' in data['message'].lower()

def test_provide_input_not_found(app, auth_client):
    """Test provide_input endpoint with non-existent execution ID"""
    with app.app_context():
        # Prepare request data
        input_data = {
            'input': 'test input'
        }
        
        # Mock the provide_input method to raise ValueError
        with patch.object(execution_service, 'provide_input') as mock_provide_input:
            # Configure mock to raise ValueError (execution not found or not waiting for input)
            mock_provide_input.side_effect = ValueError("Execution not found or not waiting for input")
            
            # Make request with invalid execution ID
            response = auth_client.post('/api/provide_input/999', json=input_data)
            
            # Check response
            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'execution not found' in data['message'].lower() or 'not waiting for input' in data['message'].lower()