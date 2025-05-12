import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
from app.services.execution_adapter import execution_adapter, ExecutionAdapter
from app.models.execution_orm import ExecutionORM
from tests.utils import create_user, create_script, create_aws_profile

def test_execution_adapter_initialization():
    """Test execution adapter initialization"""
    adapter = ExecutionAdapter()
    assert adapter.use_orm is True

def test_get_by_id(app):
    """Test get_by_id method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Completed",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )
        execution_id = execution.save()
        
        # Test get_by_id method of adapter
        result = execution_adapter.get_by_id(execution_id)
        
        # Verify result
        assert result is not None
        assert result.id == execution_id
        assert result.script_id == script.id
        assert result.status == "Completed"
        
        # Test non-existent ID
        result = execution_adapter.get_by_id(9999)
        assert result is None

def test_get_by_id_with_details(app):
    """Test get_by_id_with_details method"""
    with app.app_context():
        # Create test data
        user = create_user(username="testuser")
        script = create_script(name="Test Script", user_id=user.id)
        aws_profile = create_aws_profile(name="Test Profile")
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Completed",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            output="Test output"
        )
        execution_id = execution.save()
        
        # Test get_by_id_with_details method
        result = execution_adapter.get_by_id_with_details(execution_id)
        
        # Verify result contains expected fields
        assert result is not None
        assert isinstance(result, dict)
        assert result['id'] == execution_id
        assert result['script_id'] == script.id
        assert result['aws_profile_id'] == aws_profile.id
        assert result['user_id'] == user.id
        assert result['status'] == "Completed"
        assert result['output'] == "Test output"
        
        # Verify related data
        assert result['script_name'] == "Test Script"
        assert result['aws_profile_name'] == "Test Profile"
        assert result['username'] == "testuser"
        
        # Test non-existent ID
        result = execution_adapter.get_by_id_with_details(9999)
        assert result is None

def test_get_recent(app):
    """Test get_recent method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create multiple executions
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
        
        # Test get_recent with default limit (should return all created executions, which is 5)
        results = execution_adapter.get_recent()
        assert len(results) == 5  # We created 5 executions
        
        # Test get_recent with custom limit
        results = execution_adapter.get_recent(limit=3)
        assert len(results) == 3
        
        # Verify results are sorted by ID descending (newest first)
        if len(results) >= 2:
            assert results[0]['id'] > results[1]['id']

def test_get_history(app):
    """Test get_history method with pagination and filters"""
    with app.app_context():
        # Create test data
        user = create_user()
        script1 = create_script(name="Script 1", user_id=user.id)
        script2 = create_script(name="Script 2", user_id=user.id)
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
        
        # Test get_history with default parameters
        results = execution_adapter.get_history()
        assert 'executions' in results
        assert 'total_count' in results
        assert 'total_pages' in results
        assert 'current_page' in results
        assert results['current_page'] == 1
        
        # Test get_history with custom pagination
        results = execution_adapter.get_history(page=2, per_page=3)
        assert results['current_page'] == 2
        assert len(results['executions']) <= 3
        
        # Test get_history with filters
        results = execution_adapter.get_history(filters={'status': 'Failed'})
        assert all(e['status'] == 'Failed' for e in results['executions'])
        
        results = execution_adapter.get_history(filters={'script_id': script1.id})
        assert all(e['script_id'] == script1.id for e in results['executions'])
        
        # Test combined filters
        results = execution_adapter.get_history(
            filters={'script_id': script2.id, 'status': 'Failed'}
        )
        assert all(e['script_id'] == script2.id and e['status'] == 'Failed' 
                 for e in results['executions'])

def test_get_stats(app):
    """Test get_stats method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create executions with different statuses
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
        
        # Test get_stats with default days
        stats = execution_adapter.get_stats()
        assert isinstance(stats, list)
        assert len(stats) > 0
        
        # Test get_stats with custom days
        stats = execution_adapter.get_stats(days=3)
        assert len(stats) <= 3
        
        # Find today's stats
        today_date = datetime.now().strftime('%Y-%m-%d')
        today_stats = next((s for s in stats if s['date'] == today_date), None)
        
        # Verify today's stats
        if today_stats:
            assert today_stats['Success'] >= 3
            assert today_stats['Failed'] >= 2

def test_create(app):
    """Test create method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Test create method with minimal parameters
        execution_id = execution_adapter.create(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id
        )
        
        # Verify execution was created
        assert execution_id is not None
        
        # Retrieve created execution
        execution = ExecutionORM.get_by_id(execution_id)
        assert execution is not None
        assert execution.script_id == script.id
        assert execution.aws_profile_id == aws_profile.id
        assert execution.user_id == user.id
        assert execution.status == "Pending"
        assert execution.start_time is not None
        assert execution.is_scheduled == 0
        
        # Test create method with all parameters
        parameters = {'param1': 'value1', 'param2': 'value2'}
        custom_start_time = datetime.now().isoformat()
        
        execution_id = execution_adapter.create(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=custom_start_time,
            parameters=json.dumps(parameters),
            is_scheduled=1
        )
        
        # Verify execution was created with custom parameters
        execution = ExecutionORM.get_by_id(execution_id)
        assert execution is not None
        assert execution.script_id == script.id
        assert execution.status == "Running"
        assert execution.start_time == custom_start_time
        assert execution.parameters == json.dumps(parameters)
        assert execution.is_scheduled == 1

def test_update_status(app):
    """Test update_status method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running"
        )
        execution_id = execution.save()
        
        # Test update_status without output
        result = execution_adapter.update_status(execution_id, "Completed")
        assert result is True
        
        # Verify status was updated
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.status == "Completed"
        
        # Test update_status with output
        result = execution_adapter.update_status(
            execution_id, 
            "Failed", 
            output="Error occurred during execution"
        )
        assert result is True
        
        # Verify status and output were updated
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.status == "Failed"
        assert updated_execution.output == "Error occurred during execution"
        
        # Test update_status with non-existent ID
        result = execution_adapter.update_status(9999, "Completed")
        assert result is False
        
        # Test update_status with execution returned as dict
        with patch('app.models.execution_orm.ExecutionORM.get_by_id') as mock_get_by_id, \
             patch('app.utils.db.db.session.get') as mock_session_get:
            
            # Create mock execution object
            mock_execution = MagicMock()
            mock_execution.update_status.return_value = True
            
            # Configure mock to return a dict first, then the actual ORM object
            mock_get_by_id.return_value = {'id': execution_id, 'status': 'Running'}
            mock_session_get.return_value = mock_execution
            
            # Test update_status when get_by_id returns a dict
            result = execution_adapter.update_status(execution_id, "Completed")
            
            # Verify correct methods were called
            assert result is True
            mock_get_by_id.assert_called_once_with(execution_id)
            mock_session_get.assert_called_once()
            mock_execution.update_status.assert_called_once_with("Completed", None)

def test_append_output(app):
    """Test append_output method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            output="Initial output"
        )
        execution_id = execution.save()
        
        # Test append_output
        result = execution_adapter.append_output(execution_id, "\nAdditional output")
        assert result is True
        
        # Verify output was appended
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.output == "Initial output\nAdditional output"
        
        # Test append_output with non-existent ID
        result = execution_adapter.append_output(9999, "Output")
        assert result is False
        
        # Test append_output with execution returned as dict
        with patch('app.models.execution_orm.ExecutionORM.get_by_id') as mock_get_by_id, \
             patch('app.utils.db.db.session.get') as mock_session_get:
            
            # Create mock execution object
            mock_execution = MagicMock()
            mock_execution.append_output.return_value = True
            
            # Configure mock to return a dict first, then the actual ORM object
            mock_get_by_id.return_value = {'id': execution_id, 'output': 'Current output'}
            mock_session_get.return_value = mock_execution
            
            # Test append_output when get_by_id returns a dict
            result = execution_adapter.append_output(execution_id, "\nMore output")
            
            # Verify correct methods were called
            assert result is True
            mock_get_by_id.assert_called_once_with(execution_id)
            mock_session_get.assert_called_once()
            mock_execution.append_output.assert_called_once_with("\nMore output")

def test_update_ai_analysis(app):
    """Test update_ai_analysis method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Failed",
            output="Error: Something went wrong"
        )
        execution_id = execution.save()
        
        # Test update_ai_analysis
        result = execution_adapter.update_ai_analysis(
            execution_id,
            "Script failed due to permission issues",
            "Try running with elevated permissions"
        )
        assert result is True
        
        # Verify AI analysis was updated
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.ai_analysis == "Script failed due to permission issues"
        assert updated_execution.ai_solution == "Try running with elevated permissions"
        
        # Test update_ai_analysis with non-existent ID
        result = execution_adapter.update_ai_analysis(9999, "Analysis", "Solution")
        assert result is False
        
        # Test update_ai_analysis with execution returned as dict
        with patch('app.models.execution_orm.ExecutionORM.get_by_id') as mock_get_by_id, \
             patch('app.utils.db.db.session.get') as mock_session_get:
            
            # Create mock execution object
            mock_execution = MagicMock()
            mock_execution.update_ai_analysis.return_value = True
            
            # Configure mock to return a dict first, then the actual ORM object
            mock_get_by_id.return_value = {'id': execution_id}
            mock_session_get.return_value = mock_execution
            
            # Test update_ai_analysis when get_by_id returns a dict
            result = execution_adapter.update_ai_analysis(
                execution_id, 
                "New analysis",
                "New solution"
            )
            
            # Verify correct methods were called
            assert result is True
            mock_get_by_id.assert_called_once_with(execution_id)
            mock_session_get.assert_called_once()
            mock_execution.update_ai_analysis.assert_called_once_with("New analysis", "New solution")

def test_cancel(app):
    """Test cancel method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution in running state
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=datetime.now().isoformat(),
            output="Running script..."
        )
        execution_id = execution.save()
        
        # Test cancel
        result = execution_adapter.cancel(execution_id)
        assert result is True
        
        # Verify execution was cancelled
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.status == "Cancelled"
        assert updated_execution.end_time is not None
        assert "[SYSTEM] Script execution was cancelled by user." in updated_execution.output
        
        # Test cancel with non-existent ID
        result = execution_adapter.cancel(9999)
        assert result is False
        
        # Test cancel with execution returned as dict
        with patch('app.models.execution_orm.ExecutionORM.get_by_id') as mock_get_by_id, \
             patch('app.utils.db.db.session.get') as mock_session_get:
            
            # Create mock execution object
            mock_execution = MagicMock()
            mock_execution.cancel.return_value = True
            
            # Configure mock to return a dict first, then the actual ORM object
            mock_get_by_id.return_value = {'id': execution_id, 'status': 'Running'}
            mock_session_get.return_value = mock_execution
            
            # Test cancel when get_by_id returns a dict
            result = execution_adapter.cancel(execution_id)
            
            # Verify correct methods were called
            assert result is True
            mock_get_by_id.assert_called_once_with(execution_id)
            mock_session_get.assert_called_once()
            mock_execution.cancel.assert_called_once()
            
        # Test cancel for a non-running execution
        non_running_execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Pending"
        )
        non_running_id = non_running_execution.save()
        
        result = execution_adapter.cancel(non_running_id)
        assert result is False

def test_parse_parameters(app):
    """Test parse_parameters method"""
    with app.app_context():
        # Create test data
        user = create_user()
        script = create_script(user_id=user.id)
        aws_profile = create_aws_profile()
        
        # Create test execution with parameters
        params = {'param1': 'value1', 'param2': 'value2'}
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            parameters=json.dumps(params)
        )
        execution_id = execution.save()
        
        # Test parse_parameters with ExecutionORM instance
        result = execution_adapter.parse_parameters(execution)
        assert result == params
        
        # Test parse_parameters with execution ID
        result = execution_adapter.parse_parameters(execution_id)
        assert result == params
        
        # Test parse_parameters with non-existent ID
        result = execution_adapter.parse_parameters(9999)
        assert result == {}
        
        # Test parse_parameters with invalid input
        result = execution_adapter.parse_parameters("not an execution or id")
        assert result == {}