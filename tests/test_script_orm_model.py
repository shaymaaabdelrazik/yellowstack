import pytest
import json
from app.models.script_orm import ScriptORM
from app.models.user_orm import UserORM
from app.utils.db import db
from tests.utils import create_user

def test_script_creation(app):
    """Test creating a new script"""
    with app.app_context():
        # Create a new script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        
        # Save script to database
        script_id = script.save()
        
        # Verify script was created
        assert script_id is not None
        assert script.id is not None
        assert script.name == 'Test Script'
        assert script.description == 'A test script'
        assert script.path == '/path/to/script.py'
        assert script.parameters == json.dumps([{'name': 'test_param', 'default': 'test_value'}])
        assert script.user_id == 1

def test_get_by_id(app):
    """Test retrieving a script by ID"""
    with app.app_context():
        # Create test script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        script_id = script.save()
        
        # Retrieve script by ID
        retrieved_script = ScriptORM.get_by_id(script_id)
        
        # Verify script was retrieved correctly
        assert retrieved_script is not None
        assert retrieved_script.id == script_id
        assert retrieved_script.name == 'Test Script'
        assert retrieved_script.description == 'A test script'
        assert retrieved_script.path == '/path/to/script.py'
        assert retrieved_script.parameters == json.dumps([{'name': 'test_param', 'default': 'test_value'}])
        assert retrieved_script.user_id == 1

def test_get_by_id_not_found(app):
    """Test retrieving a non-existent script"""
    with app.app_context():
        # Try to retrieve a script with a non-existent ID
        script = ScriptORM.get_by_id(999)
        
        # Verify no script was found
        assert script is None

def test_get_all(app):
    """Test retrieving all scripts"""
    with app.app_context():
        # Create a user
        user = create_user(username='testuser', password='password123', is_admin=1)
        
        # Create test scripts
        script1 = ScriptORM(
            name='Test Script 1',
            description='First test script',
            path='/path/to/script1.py',
            parameters=json.dumps([{'name': 'param1', 'default': 'value1'}]),
            user_id=user.id
        )
        script1.save()
        
        script2 = ScriptORM(
            name='Test Script 2',
            description='Second test script',
            path='/path/to/script2.py',
            parameters=json.dumps([{'name': 'param2', 'default': 'value2'}]),
            user_id=user.id
        )
        script2.save()
        
        # Retrieve all scripts
        scripts = ScriptORM.get_all()
        
        # Verify scripts were retrieved correctly
        assert len(scripts) == 2
        
        # Get script names
        script_names = [script.get('name') for script in scripts]
        assert 'Test Script 1' in script_names
        assert 'Test Script 2' in script_names
        
        # Verify username is included
        for script in scripts:
            assert script.get('username') == 'testuser'

def test_get_all_no_user(app):
    """Test retrieving scripts with no associated user"""
    with app.app_context():
        # Create test script with no user
        script = ScriptORM(
            name='Orphan Script',
            description='Script with no user',
            path='/path/to/orphan.py',
            parameters=json.dumps([{'name': 'param', 'default': 'value'}]),
            user_id=None
        )
        script.save()
        
        # Retrieve all scripts
        scripts = ScriptORM.get_all()
        
        # Verify scripts were retrieved correctly
        assert len(scripts) > 0
        
        # Find the orphan script
        orphan_script = next((s for s in scripts if s.get('name') == 'Orphan Script'), None)
        assert orphan_script is not None
        
        # Verify username is None
        assert orphan_script.get('username') is None

def test_save_new(app):
    """Test saving a new script"""
    with app.app_context():
        # Create a new script
        script = ScriptORM(
            name='New Script',
            description='A new script',
            path='/path/to/new.py',
            parameters=json.dumps([{'name': 'new_param', 'default': 'new_value'}]),
            user_id=1
        )
        
        # Save the script
        script_id = script.save()
        
        # Verify script was saved correctly
        assert script_id is not None
        
        # Retrieve script from database
        saved_script = ScriptORM.get_by_id(script_id)
        assert saved_script is not None
        assert saved_script.name == 'New Script'
        assert saved_script.description == 'A new script'
        assert saved_script.path == '/path/to/new.py'

def test_save_update(app):
    """Test updating an existing script"""
    with app.app_context():
        # Create and save a script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        script_id = script.save()
        
        # Update the script
        script.name = 'Updated Script'
        script.description = 'Updated description'
        script.save()
        
        # Verify script was updated
        updated_script = ScriptORM.get_by_id(script_id)
        assert updated_script.name == 'Updated Script'
        assert updated_script.description == 'Updated description'

def test_delete(app):
    """Test deleting a script"""
    with app.app_context():
        # Create a script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        script_id = script.save()
        
        # Verify script exists
        assert ScriptORM.get_by_id(script_id) is not None
        
        # Delete the script
        result = script.delete()
        
        # Verify deletion was successful
        assert result is True
        
        # Verify script no longer exists
        assert ScriptORM.get_by_id(script_id) is None

def test_exists(app):
    """Test checking if a script name exists"""
    with app.app_context():
        # Create a script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        script.save()
        
        # Check existing script name
        assert ScriptORM.exists('Test Script') is True
        
        # Check non-existent script name
        assert ScriptORM.exists('Nonexistent Script') is False

def test_to_dict(app):
    """Test converting script to dictionary"""
    with app.app_context():
        # Create a script
        script = ScriptORM(
            name='Test Script',
            description='A test script',
            path='/path/to/script.py',
            parameters=json.dumps([{'name': 'test_param', 'default': 'test_value'}]),
            user_id=1
        )
        script.save()
        
        # Get dictionary representation
        script_dict = script.to_dict()
        
        # Verify dictionary contains expected fields
        assert 'id' in script_dict
        assert 'name' in script_dict
        assert 'description' in script_dict
        assert 'path' in script_dict
        assert 'parameters' in script_dict
        assert 'user_id' in script_dict
        
        # Verify values are correct
        assert script_dict['name'] == 'Test Script'
        assert script_dict['description'] == 'A test script'
        assert script_dict['path'] == '/path/to/script.py'
        assert script_dict['parameters'] == json.dumps([{'name': 'test_param', 'default': 'test_value'}])
        assert script_dict['user_id'] == 1

def test_parse_parameters(app):
    """Test parsing parameters JSON string"""
    with app.app_context():
        # Create a script with parameters
        params = [{'name': 'test_param', 'default': 'test_value'}]
        script = ScriptORM(
            name='Test Script',
            parameters=json.dumps(params)
        )
        
        # Parse parameters
        parsed_params = script.parse_parameters()
        
        # Verify parameters were parsed correctly
        assert parsed_params == params
        
        # Test with empty parameters
        script.parameters = None
        assert script.parse_parameters() == []
        
        script.parameters = ''
        assert script.parse_parameters() == []
        
        # Test with invalid JSON
        script.parameters = 'invalid json'
        assert script.parse_parameters() == []