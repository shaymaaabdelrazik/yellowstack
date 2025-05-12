import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.services.script_service import script_service
from app.models.script_orm import ScriptORM
from tests.utils import create_user, create_script

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

@pytest.fixture
def invalid_python_script():
    """Create a temporary invalid Python script for testing"""
    script_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    script_file.write(b'this is not valid python code!')
    script_file.close()
    
    yield script_file.name
    
    # Clean up
    if os.path.exists(script_file.name):
        os.unlink(script_file.name)

def test_get_all_scripts(app):
    """Test retrieving all scripts"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test scripts
        script1 = create_script(name='Script 1', user_id=user.id)
        script2 = create_script(name='Script 2', user_id=user.id)
        
        # Get all scripts
        scripts = script_service.get_all_scripts()
        
        # Verify scripts were retrieved correctly
        assert len(scripts) >= 2
        
        # Get script names
        script_names = [script.get('name') for script in scripts]
        assert 'Script 1' in script_names
        assert 'Script 2' in script_names

def test_get_script_by_id(app):
    """Test retrieving a script by ID"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(name='Test Script', user_id=user.id)
        
        # Get script by ID
        retrieved_script = script_service.get_script_by_id(script.id)
        
        # Verify script was retrieved correctly
        assert retrieved_script is not None
        assert retrieved_script.id == script.id
        assert retrieved_script.name == 'Test Script'

def test_get_script_by_id_not_found(app):
    """Test retrieving a non-existent script"""
    with app.app_context():
        # Get script by non-existent ID
        script = script_service.get_script_by_id(999)
        
        # Verify no script was found
        assert script is None

def test_create_script(app, temp_python_script):
    """Test creating a new script"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create a new script
        script_id = script_service.create_script(
            name='New Script',
            description='A new script',
            path=temp_python_script,
            parameters=json.dumps([{'name': 'param1', 'default': 'value1'}]),
            user_id=user.id
        )
        
        # Verify script was created
        assert script_id is not None
        
        # Verify script was saved to database
        script = ScriptORM.get_by_id(script_id)
        assert script is not None
        assert script.name == 'New Script'
        assert script.description == 'A new script'
        assert script.path == temp_python_script
        assert script.parameters == json.dumps([{'name': 'param1', 'default': 'value1'}])
        assert script.user_id == user.id

def test_create_script_duplicate_name(app, temp_python_script):
    """Test creating a script with a duplicate name"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create initial script
        script_service.create_script(
            name='Duplicate Script',
            description='First script',
            path=temp_python_script,
            user_id=user.id
        )
        
        # Try to create another script with the same name
        with pytest.raises(ValueError) as excinfo:
            script_service.create_script(
                name='Duplicate Script',
                description='Second script',
                path=temp_python_script,
                user_id=user.id
            )
        
        # Verify error message
        assert "already exists" in str(excinfo.value)

def test_create_script_invalid_path(app):
    """Test creating a script with an invalid path"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Try to create a script with non-existent path
        with pytest.raises(ValueError) as excinfo:
            script_service.create_script(
                name='Invalid Path Script',
                description='A script with invalid path',
                path='/nonexistent/path.py',
                user_id=user.id
            )
        
        # Verify error message
        assert "not found" in str(excinfo.value)

def test_create_script_non_python_file(app, temp_python_script):
    """Test creating a script with a non-Python file"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create a non-Python file
        non_py_file = temp_python_script.replace('.py', '.txt')
        with open(non_py_file, 'w') as f:
            f.write('This is not a Python file')
        
        try:
            # Try to create a script with non-Python file
            with pytest.raises(ValueError) as excinfo:
                script_service.create_script(
                    name='Non-Python Script',
                    description='A non-Python script',
                    path=non_py_file,
                    user_id=user.id
                )
            
            # Verify error message
            assert "must be a Python file" in str(excinfo.value)
        finally:
            # Clean up
            if os.path.exists(non_py_file):
                os.unlink(non_py_file)

def test_create_script_invalid_python(app, invalid_python_script):
    """Test creating a script with invalid Python code"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Try to create a script with invalid Python code
        with pytest.raises(ValueError) as excinfo:
            script_service.create_script(
                name='Invalid Python Script',
                description='A script with invalid Python code',
                path=invalid_python_script,
                user_id=user.id
            )
        
        # Verify error message
        assert "could not be imported" in str(excinfo.value)

def test_update_script(app, temp_python_script):
    """Test updating a script"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(name='Original Script', user_id=user.id)
        
        # Update the script
        success = script_service.update_script(
            script_id=script.id,
            name='Updated Script',
            description='Updated description',
            path=temp_python_script,
            parameters=json.dumps([{'name': 'new_param', 'default': 'new_value'}])
        )
        
        # Verify update was successful
        assert success is True
        
        # Verify script was updated in database
        updated_script = ScriptORM.get_by_id(script.id)
        assert updated_script.name == 'Updated Script'
        assert updated_script.description == 'Updated description'
        assert updated_script.path == temp_python_script
        assert updated_script.parameters == json.dumps([{'name': 'new_param', 'default': 'new_value'}])

def test_update_script_partial(app, temp_python_script):
    """Test partially updating a script"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(
            name='Original Script', 
            description='Original description',
            path=temp_python_script,
            parameters=json.dumps([{'name': 'orig_param', 'default': 'orig_value'}]),
            user_id=user.id
        )
        
        # Update only the name
        success = script_service.update_script(
            script_id=script.id,
            name='Updated Script'
        )
        
        # Verify update was successful
        assert success is True
        
        # Verify only name was updated in database
        updated_script = ScriptORM.get_by_id(script.id)
        assert updated_script.name == 'Updated Script'
        assert updated_script.description == 'Original description'
        assert updated_script.path == temp_python_script
        assert updated_script.parameters == json.dumps([{'name': 'orig_param', 'default': 'orig_value'}])

def test_update_script_not_found(app, temp_python_script):
    """Test updating a non-existent script"""
    with app.app_context():
        # Try to update a non-existent script
        with pytest.raises(ValueError) as excinfo:
            script_service.update_script(
                script_id=999,
                name='Updated Script',
                description='Updated description',
                path=temp_python_script
            )
        
        # Verify error message
        assert "not found" in str(excinfo.value)

def test_delete_script(app):
    """Test deleting a script"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(name='Test Script', user_id=user.id)
        
        # Verify script exists
        assert ScriptORM.get_by_id(script.id) is not None
        
        # Delete the script
        success = script_service.delete_script(script.id)
        
        # Verify deletion was successful
        assert success is True
        
        # Verify script no longer exists
        assert ScriptORM.get_by_id(script.id) is None

def test_delete_script_not_found(app):
    """Test deleting a non-existent script"""
    with app.app_context():
        # Try to delete a non-existent script
        with pytest.raises(ValueError) as excinfo:
            script_service.delete_script(999)
        
        # Verify error message
        assert "not found" in str(excinfo.value)

@patch('app.services.script_adapter.ScriptAdapter.delete')
def test_delete_script_with_executions(mock_delete, app):
    """Test deleting a script that has executions"""
    # Mock the delete method to return False (simulating a script with executions)
    mock_delete.return_value = False
    
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(name='Test Script', user_id=user.id)
        
        # Delete the script
        success = script_service.delete_script(script.id)
        
        # Verify deletion failed (script has executions)
        assert success is False
        
        # Verify delete was called with correct ID
        mock_delete.assert_called_once_with(script.id)

def test_parse_script_parameters(app):
    """Test parsing script parameters from JSON string"""
    with app.app_context():
        # Valid JSON parameters
        params = [{'name': 'param1', 'default': 'value1'}, {'name': 'param2', 'default': 'value2'}]
        params_json = json.dumps(params)
        
        # Parse parameters
        parsed_params = script_service.parse_script_parameters(params_json)
        
        # Verify parameters were parsed correctly
        assert parsed_params == params
        
        # Empty parameters
        assert script_service.parse_script_parameters('') == []
        assert script_service.parse_script_parameters(None) == []
        
        # Invalid JSON
        assert script_service.parse_script_parameters('invalid json') == []

def test_collect_script_parameters(app):
    """Test collecting script parameters from form data"""
    with app.app_context():
        # Create form data
        form_data = {
            'param-name-1': 'param1',
            'param-default-1': 'value1',
            'param-name-2': 'param2',
            'param-default-2': 'value2',
            'param-name-3': 'param3',
            'param-default-3': '',
            'other-field': 'other-value'
        }
        
        # Collect parameters
        params = script_service.collect_script_parameters(form_data)
        
        # Verify parameters were collected correctly
        assert len(params) == 3
        assert params[0] == {'name': 'param1', 'default': 'value1'}
        assert params[1] == {'name': 'param2', 'default': 'value2'}
        assert params[2] == {'name': 'param3', 'default': ''}
        
        # Form data with gaps
        form_data_with_gaps = {
            'param-name-1': 'param1',
            'param-default-1': 'value1',
            'param-name-3': 'param3',  # Skip param-name-2
            'param-default-3': 'value3'
        }
        
        params = script_service.collect_script_parameters(form_data_with_gaps)
        
        # Verify parameters were collected correctly
        assert len(params) == 2
        assert params[0] == {'name': 'param1', 'default': 'value1'}
        assert params[1] == {'name': 'param3', 'default': 'value3'}
        
        # Empty form data
        assert script_service.collect_script_parameters({}) == []