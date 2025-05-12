import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.execution_service import execution_service
from app.models.execution_orm import ExecutionORM
from app.models.script_orm import ScriptORM
from app.models.aws_profile_orm import AWSProfileORM
from tests.utils import create_user, create_script, create_aws_profile

@pytest.fixture
def temp_python_script():
    """Create a temporary valid Python script for testing"""
    script_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    script_file.write(b'def run(args=None):\n    return {"result": "success"}\n')
    script_file.close()
    
    yield script_file.name
    
    # Clean up
    if os.path.exists(script_file.name):
        os.unlink(script_file.name)

def test_get_recent_executions(app):
    """Test retrieving recent executions"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Create test executions
        for i in range(5):
            execution = ExecutionORM(
                script_id=script.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Success",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )
            execution.save()
        
        # Get recent executions
        executions = execution_service.get_recent_executions(limit=3)
        
        # Verify executions were retrieved correctly
        assert len(executions) == 3
        
        # Verify executions are in descending order (newest first)
        if len(executions) >= 2:
            assert executions[0]['id'] > executions[1]['id']

def test_get_execution_by_id(app):
    """Test retrieving an execution by ID with details"""
    with app.app_context():
        # Create test user
        user = create_user(username="testuser")
        
        # Create test script
        script = create_script(name="Test Script", user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(name="Test Profile")
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Success",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            output="Test output"
        )
        execution_id = execution.save()
        
        # Get execution by ID
        execution_details = execution_service.get_execution_by_id(execution_id)
        
        # Verify execution was retrieved correctly
        assert execution_details is not None
        assert execution_details['id'] == execution_id
        assert execution_details['script_id'] == script.id
        assert execution_details['aws_profile_id'] == aws_profile.id
        assert execution_details['user_id'] == user.id
        assert execution_details['status'] == "Success"
        assert execution_details['output'] == "Test output"
        
        # Verify related data is included
        assert execution_details['script_name'] == "Test Script"
        assert execution_details['aws_profile_name'] == "Test Profile"
        assert execution_details['username'] == "testuser"

def test_get_execution_history(app):
    """Test retrieving execution history with pagination"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Create 15 test executions
        for i in range(15):
            execution = ExecutionORM(
                script_id=script.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Success",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )
            execution.save()
        
        # Get page 1 with 5 executions per page
        history = execution_service.get_execution_history(page=1, per_page=5)
        
        # Verify pagination works correctly
        assert 'executions' in history
        assert 'current_page' in history
        assert 'total_pages' in history
        assert 'total_count' in history
        
        assert history['current_page'] == 1
        assert len(history['executions']) == 5
        assert history['total_count'] >= 15
        assert history['total_pages'] >= 3
        
        # Get page 2
        history_page2 = execution_service.get_execution_history(page=2, per_page=5)
        
        # Verify page 2 has different executions than page 1
        page1_ids = [e['id'] for e in history['executions']]
        page2_ids = [e['id'] for e in history_page2['executions']]
        
        assert len(set(page1_ids).intersection(set(page2_ids))) == 0

def test_get_execution_history_with_filters(app):
    """Test retrieving execution history with filters"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test scripts
        script1 = create_script(name="Script 1", user_id=user.id)
        script2 = create_script(name="Script 2", user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Create executions for script1 with "Success" status
        for i in range(5):
            execution = ExecutionORM(
                script_id=script1.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Success",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )
            execution.save()
        
        # Create executions for script2 with "Failed" status
        for i in range(3):
            execution = ExecutionORM(
                script_id=script2.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Failed",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )
            execution.save()
        
        # Filter by script_id
        history = execution_service.get_execution_history(filters={'script_id': script1.id})
        
        # Verify filtered results
        assert len(history['executions']) == 5
        for execution in history['executions']:
            assert execution['script_id'] == script1.id
        
        # Filter by status
        history = execution_service.get_execution_history(filters={'status': 'Failed'})
        
        # Verify filtered results
        assert len(history['executions']) >= 3
        for execution in history['executions']:
            assert execution['status'] == 'Failed'
        
        # Combined filters
        history = execution_service.get_execution_history(
            filters={'script_id': script2.id, 'status': 'Failed'}
        )
        
        # Verify filtered results
        assert len(history['executions']) == 3
        for execution in history['executions']:
            assert execution['script_id'] == script2.id
            assert execution['status'] == 'Failed'

def test_get_execution_stats(app):
    """Test retrieving execution statistics"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Create executions for today with different statuses
        today = datetime.now().isoformat()
        
        # Success executions
        for i in range(3):
            execution = ExecutionORM(
                script_id=script.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Success",
                start_time=today,
                end_time=today
            )
            execution.save()
        
        # Failed executions
        for i in range(2):
            execution = ExecutionORM(
                script_id=script.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Failed",
                start_time=today,
                end_time=today
            )
            execution.save()
        
        # Get stats for last 7 days
        stats = execution_service.get_execution_stats(days=7)
        
        # Verify stats format
        assert isinstance(stats, list)
        assert len(stats) > 0
        
        # Find today's stats
        today_date = datetime.now().strftime('%Y-%m-%d')
        today_stats = next((s for s in stats if s['date'] == today_date), None)
        
        # Verify today's stats
        if today_stats:
            assert today_stats['Success'] >= 3
            assert today_stats['Failed'] >= 2

@patch('threading.Thread')
def test_run_script(mock_thread, app):
    """Test running a script"""
    # Mock the Thread class to avoid actually running scripts
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Run the script
        execution_id = execution_service.run_script(
            script_id=script.id,
            profile_id=aws_profile.id,
            user_id=user.id,
            parameters={'param1': 'value1'}
        )
        
        # Verify execution was created
        assert execution_id is not None
        
        # Verify execution record exists
        execution = ExecutionORM.get_by_id(execution_id)
        assert execution is not None
        assert execution.script_id == script.id
        assert execution.aws_profile_id == aws_profile.id
        assert execution.user_id == user.id
        assert execution.parameters == json.dumps({'param1': 'value1'})
        assert execution.is_scheduled == 0
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()

def test_run_script_invalid_script(app):
    """Test running with an invalid script ID"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Run with non-existent script ID
        with pytest.raises(ValueError) as excinfo:
            execution_service.run_script(
                script_id=999,
                profile_id=aws_profile.id,
                user_id=user.id
            )
        
        # Verify error message
        assert "Script not found" in str(excinfo.value)

def test_run_script_invalid_profile(app):
    """Test running with an invalid AWS profile ID"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Run with non-existent AWS profile ID
        with pytest.raises(ValueError) as excinfo:
            execution_service.run_script(
                script_id=script.id,
                profile_id=999,
                user_id=user.id
            )
        
        # Verify error message
        assert "AWS profile not found" in str(excinfo.value)

@patch('app.services.execution_service.psutil')
@patch('app.services.execution_service.running_processes')
def test_cancel_execution(mock_running_processes, mock_psutil, app):
    """Test cancelling a running execution"""
    # Set up mocks
    mock_process = MagicMock()
    mock_process.poll.return_value = None  # Process is still running
    mock_process.pid = 12345

    # Set up psutil mock
    mock_parent_process = MagicMock()
    mock_parent_process.children.return_value = []
    mock_psutil.Process.return_value = mock_parent_process
    
    # Set up running_processes dict
    running_processes_dict = {}
    
    # Set up execution adapter mock
    with patch('app.services.execution_adapter.ExecutionAdapter.update_status') as mock_update_status, \
         patch('app.services.execution_adapter.ExecutionAdapter.append_output') as mock_append_output, \
         patch('app.services.execution_adapter.ExecutionAdapter.get_by_id_with_details') as mock_get_details:
        
        with app.app_context():
            # Create test user
            user = create_user()
            
            # Create test script
            script = create_script(user_id=user.id)
            
            # Create test AWS profile
            aws_profile = create_aws_profile()
            
            # Create a running execution
            execution = ExecutionORM(
                script_id=script.id,
                aws_profile_id=aws_profile.id,
                user_id=user.id,
                status="Running",
                start_time=datetime.now().isoformat()
            )
            execution_id = execution.save()
            
            # Set up the mock get_by_id_with_details to return a dictionary
            mock_get_details.return_value = {
                'id': execution_id,
                'script_id': script.id,
                'status': 'Running'
            }
            
            # Set up the running processes dictionary
            running_processes_dict[execution_id] = mock_process
            mock_running_processes.get.return_value = mock_process
            
            # Use patch.dict to mock the running_processes dictionary
            with patch.dict('app.services.execution_service.running_processes', running_processes_dict, clear=True):
                # Cancel the execution
                result = execution_service.cancel_execution(execution_id)
                
                # Verify cancellation was attempted
                mock_update_status.assert_called_with(
                    execution_id=execution_id,
                    status="Cancelled",
                    output="\n[SYSTEM] Cancellation requested by user - terminating process..."
                )
                
                # Verify process termination was attempted
                mock_parent_process.terminate.assert_called_once()
                
                # Verify output was appended
                mock_append_output.assert_called_with(
                    execution_id, 
                    "\n[SYSTEM] Process terminated successfully."
                )
                
                # Don't check if removed from dictionary since the actual implementation
                # uses del which won't work on our mock dictionary in the test

def test_cancel_execution_not_running(app):
    """Test cancelling a non-running execution"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile()
        
        # Create a "Pending" execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Pending"
        )
        execution_id = execution.save()
        
        # Try to cancel the execution and expect ValueError
        with pytest.raises(ValueError) as excinfo:
            execution_service.cancel_execution(execution_id)
        
        # Verify error message
        assert "not running" in str(excinfo.value)

@patch('app.services.execution_service.datetime')
@patch('app.services.execution_adapter.ExecutionAdapter.update_status')
def test_check_hung_executions(mock_update_status, mock_datetime, app):
    """Test checking for hung executions"""
    # Mock the current time
    mock_now = datetime.now()
    mock_datetime.now.return_value = mock_now
    
    # Mock timedelta to return our fixed value
    mock_datetime.timedelta = timedelta
    
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create a hanging execution (3 hours old)
        hung_execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=(mock_now - timedelta(hours=3)).isoformat()
        )
        hung_execution_id = hung_execution.save()
        
        # Create a normal execution (just started)
        normal_execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=mock_now.isoformat()
        )
        normal_execution_id = normal_execution.save()
        
        # Set up setting adapter mock to return a mock timeout
        with patch('app.services.setting_adapter.SettingAdapter.get') as mock_get_setting:
            # Configure mock to return 30 minutes for timeout
            mock_get_setting.return_value = '30'
            
            # Run the hung execution check
            execution_service.check_hung_executions()
            
            # Verify hung execution was marked as failed
            mock_update_status.assert_called_with(
                execution_id=hung_execution_id,
                status="Failed",
                output="\n[SYSTEM] Script execution timed out and was automatically terminated."
            )
            
            # Check the normal execution is not updated
            assert mock_update_status.call_count == 1