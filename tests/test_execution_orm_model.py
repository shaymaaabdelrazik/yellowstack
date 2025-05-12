import pytest
import json
from datetime import datetime, timedelta
from app.models.execution_orm import ExecutionORM
from app.models.script_orm import ScriptORM
from app.models.user_orm import UserORM
from app.models.aws_profile_orm import AWSProfileORM
from app.utils.db import db
from tests.utils import create_user, create_script, create_aws_profile

def test_execution_creation(app):
    """Test creating a new execution"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a new execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Pending",
            parameters=json.dumps({'param1': 'value1'}),
            is_scheduled=0
        )
        
        # Save execution to database
        execution_id = execution.save()
        
        # Verify execution was created
        assert execution_id is not None
        assert execution.id is not None
        assert execution.script_id == script.id
        assert execution.aws_profile_id == aws_profile.id
        assert execution.user_id == user.id
        assert execution.status == "Pending"
        assert execution.parameters == json.dumps({'param1': 'value1'})
        assert execution.is_scheduled == 0

def test_get_by_id(app):
    """Test retrieving an execution by ID"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=datetime.now().isoformat()
        )
        execution_id = execution.save()
        
        # Retrieve execution by ID
        retrieved_execution = ExecutionORM.get_by_id(execution_id)
        
        # Verify execution was retrieved correctly
        assert retrieved_execution is not None
        assert retrieved_execution.id == execution_id
        assert retrieved_execution.script_id == script.id
        assert retrieved_execution.aws_profile_id == aws_profile.id
        assert retrieved_execution.user_id == user.id
        assert retrieved_execution.status == "Running"

def test_get_by_id_not_found(app):
    """Test retrieving a non-existent execution"""
    with app.app_context():
        # Try to retrieve an execution with a non-existent ID
        execution = ExecutionORM.get_by_id(999)
        
        # Verify no execution was found
        assert execution is None

def test_get_by_id_with_details(app):
    """Test retrieving an execution with full details"""
    with app.app_context():
        # Create test user
        user = create_user(username="testuser")
        
        # Create test script
        script = create_script(name="Test Script", user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(name="Test Profile", user_id=user.id)
        
        # Create an execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Success",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )
        execution_id = execution.save()
        
        # Retrieve execution by ID with details
        execution_details = ExecutionORM.get_by_id_with_details(execution_id)
        
        # Verify execution details were retrieved correctly
        assert execution_details is not None
        assert execution_details['id'] == execution_id
        assert execution_details['script_id'] == script.id
        assert execution_details['aws_profile_id'] == aws_profile.id
        assert execution_details['user_id'] == user.id
        assert execution_details['status'] == "Success"
        
        # Verify related data was included
        assert execution_details['script_name'] == "Test Script"
        assert execution_details['script_path'] == script.path
        assert execution_details['aws_profile_name'] == "Test Profile"
        assert execution_details['username'] == "testuser"

def test_get_recent(app):
    """Test retrieving recent executions"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
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
        
        # Retrieve recent executions
        recent_executions = ExecutionORM.get_recent(limit=3)
        
        # Verify recent executions were retrieved correctly
        assert len(recent_executions) == 3
        
        # Verify executions are in descending order (newest first)
        assert recent_executions[0]['id'] > recent_executions[1]['id']
        assert recent_executions[1]['id'] > recent_executions[2]['id']
        
        # Verify related data is included
        for execution in recent_executions:
            assert 'script_name' in execution
            assert 'aws_profile_name' in execution
            assert 'username' in execution

def test_update_status(app):
    """Test updating execution status"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Pending"
        )
        execution_id = execution.save()
        
        # Update status to Running
        execution.update_status("Running")
        
        # Verify status was updated
        assert execution.status == "Running"
        assert execution.end_time is None
        
        # Update status to Success with output
        execution.update_status("Success", output="Script completed successfully")
        
        # Verify status and output were updated
        assert execution.status == "Success"
        assert execution.end_time is not None
        assert execution.output == "Script completed successfully"
        
        # Verify in database
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.status == "Success"
        assert updated_execution.output == "Script completed successfully"

def test_append_output(app):
    """Test appending output to an execution"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running"
        )
        execution_id = execution.save()
        
        # Append output
        execution.append_output("First line of output\n")
        
        # Verify output was appended
        assert execution.output == "First line of output\n"
        
        # Append more output
        execution.append_output("Second line of output\n")
        
        # Verify output was appended
        assert execution.output == "First line of output\nSecond line of output\n"
        
        # Verify in database
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.output == "First line of output\nSecond line of output\n"

def test_update_ai_analysis(app):
    """Test updating AI analysis for an execution"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Failed",
            output="Error: Something went wrong"
        )
        execution_id = execution.save()
        
        # Update AI analysis
        execution.update_ai_analysis(
            analysis="Script failed due to permission issues",
            solution="Try running with elevated permissions"
        )
        
        # Verify AI analysis was updated
        assert execution.ai_analysis == "Script failed due to permission issues"
        assert execution.ai_solution == "Try running with elevated permissions"
        
        # Verify in database
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.ai_analysis == "Script failed due to permission issues"
        assert updated_execution.ai_solution == "Try running with elevated permissions"

def test_cancel(app):
    """Test cancelling an execution"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a running execution
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Running",
            start_time=datetime.now().isoformat(),
            output="Running script..."
        )
        execution_id = execution.save()
        
        # Cancel the execution
        result = execution.cancel()
        
        # Verify cancellation was successful
        assert result is True
        assert execution.status == "Cancelled"
        assert execution.end_time is not None
        assert "[SYSTEM] Script execution was cancelled by user." in execution.output
        
        # Verify in database
        updated_execution = ExecutionORM.get_by_id(execution_id)
        assert updated_execution.status == "Cancelled"
        
        # Try cancelling a non-running execution
        non_running_execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Pending"
        )
        non_running_execution.save()
        
        # Attempt to cancel
        result = non_running_execution.cancel()
        
        # Verify cancellation was not performed
        assert result is False
        assert non_running_execution.status == "Pending"

def test_to_dict(app):
    """Test converting execution to dictionary"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution with all fields
        start_time = datetime.now().isoformat()
        end_time = datetime.now().isoformat()
        
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Success",
            start_time=start_time,
            end_time=end_time,
            output="Script output",
            ai_analysis="Script analysis",
            ai_solution="Script solution",
            parameters=json.dumps({'param1': 'value1'}),
            is_scheduled=1
        )
        execution.save()
        
        # Get dictionary representation
        execution_dict = execution.to_dict()
        
        # Verify dictionary contains all expected fields
        assert 'id' in execution_dict
        assert 'script_id' in execution_dict
        assert 'aws_profile_id' in execution_dict
        assert 'user_id' in execution_dict
        assert 'status' in execution_dict
        assert 'start_time' in execution_dict
        assert 'end_time' in execution_dict
        assert 'output' in execution_dict
        assert 'ai_analysis' in execution_dict
        assert 'ai_solution' in execution_dict
        assert 'parameters' in execution_dict
        assert 'is_scheduled' in execution_dict
        
        # Verify values are correct
        assert execution_dict['script_id'] == script.id
        assert execution_dict['aws_profile_id'] == aws_profile.id
        assert execution_dict['user_id'] == user.id
        assert execution_dict['status'] == "Success"
        assert execution_dict['start_time'] == start_time
        assert execution_dict['end_time'] == end_time
        assert execution_dict['output'] == "Script output"
        assert execution_dict['ai_analysis'] == "Script analysis"
        assert execution_dict['ai_solution'] == "Script solution"
        assert execution_dict['parameters'] == json.dumps({'param1': 'value1'})
        assert execution_dict['is_scheduled'] == 1

def test_parse_parameters(app):
    """Test parsing parameters JSON string"""
    with app.app_context():
        # Create an execution with parameters
        params = {'param1': 'value1', 'param2': 'value2'}
        execution = ExecutionORM(parameters=json.dumps(params))
        
        # Parse parameters
        parsed_params = execution.parse_parameters()
        
        # Verify parameters were parsed correctly
        assert parsed_params == params
        
        # Test with empty parameters
        execution.parameters = None
        assert execution.parse_parameters() == {}
        
        execution.parameters = ''
        assert execution.parse_parameters() == {}
        
        # Test with invalid JSON
        execution.parameters = 'invalid json'
        assert execution.parse_parameters() == {}