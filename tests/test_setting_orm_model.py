import pytest
from app.models.setting_orm import SettingORM
from app.utils.db import db

def test_setting_creation(app):
    """Test creating a new setting"""
    with app.app_context():
        # Create a new setting
        setting = SettingORM(
            key='test_key',
            value='test_value'
        )
        
        # Save setting to database
        result = setting.save()
        
        # Verify setting was created
        assert result is True
        assert setting.key == 'test_key'
        assert setting.value == 'test_value'
        
        # Verify in database
        db_setting = SettingORM.query.filter_by(key='test_key').first()
        assert db_setting is not None
        assert db_setting.value == 'test_value'

def test_get(app):
    """Test retrieving a setting by key"""
    with app.app_context():
        # Create a setting
        SettingORM.set('test_key', 'test_value')
        
        # Retrieve setting by key
        value = SettingORM.get('test_key')
        
        # Verify setting was retrieved correctly
        assert value == 'test_value'

def test_get_with_default(app):
    """Test retrieving a non-existent setting with default value"""
    with app.app_context():
        # Retrieve non-existent setting with default
        value = SettingORM.get('nonexistent_key', default='default_value')
        
        # Verify default value was returned
        assert value == 'default_value'

def test_get_all(app):
    """Test retrieving all settings"""
    with app.app_context():
        # Clear existing settings
        SettingORM.query.delete()
        db.session.commit()
        
        # Create test settings
        SettingORM.set('key1', 'value1')
        SettingORM.set('key2', 'value2')
        SettingORM.set('key3', 'value3')
        
        # Retrieve all settings
        settings = SettingORM.get_all()
        
        # Verify settings were retrieved correctly
        assert len(settings) == 3
        assert settings['key1'] == 'value1'
        assert settings['key2'] == 'value2'
        assert settings['key3'] == 'value3'

def test_set_new(app):
    """Test setting a new value"""
    with app.app_context():
        # Clear existing settings
        SettingORM.query.delete()
        db.session.commit()
        
        # Set a new setting
        result = SettingORM.set('new_key', 'new_value')
        
        # Verify operation was successful
        assert result is True
        
        # Verify in database
        value = SettingORM.get('new_key')
        assert value == 'new_value'

def test_set_existing(app):
    """Test updating an existing setting"""
    with app.app_context():
        # Create a setting
        SettingORM.set('existing_key', 'original_value')
        
        # Update the setting
        result = SettingORM.set('existing_key', 'updated_value')
        
        # Verify operation was successful
        assert result is True
        
        # Verify in database
        value = SettingORM.get('existing_key')
        assert value == 'updated_value'

def test_update_multiple(app):
    """Test updating multiple settings at once"""
    with app.app_context():
        # Clear existing settings
        SettingORM.query.delete()
        db.session.commit()
        
        # Create some initial settings
        SettingORM.set('key1', 'value1')
        SettingORM.set('key2', 'value2')
        
        # Update multiple settings
        settings_dict = {
            'key1': 'updated_value1',  # Update existing
            'key2': 'updated_value2',  # Update existing
            'key3': 'new_value3'       # Add new
        }
        
        result = SettingORM.update_multiple(settings_dict)
        
        # Verify operation was successful
        assert result is True
        
        # Verify in database
        settings = SettingORM.get_all()
        assert settings['key1'] == 'updated_value1'
        assert settings['key2'] == 'updated_value2'
        assert settings['key3'] == 'new_value3'

def test_update_multiple_empty(app):
    """Test updating with an empty dictionary"""
    with app.app_context():
        # Update with empty dict
        result = SettingORM.update_multiple({})
        
        # Verify operation was not performed
        assert result is False

def test_save_invalid(app):
    """Test saving a setting with no key"""
    with app.app_context():
        # Create a setting without a key
        setting = SettingORM(value='test_value')
        
        # Try to save
        result = setting.save()
        
        # Verify operation failed
        assert result is False

def test_delete(app):
    """Test deleting a setting"""
    with app.app_context():
        # Create a setting
        setting = SettingORM(key='test_key', value='test_value')
        setting.save()
        
        # Verify setting exists
        assert SettingORM.get('test_key') == 'test_value'
        
        # Delete the setting
        result = setting.delete()
        
        # Verify deletion was successful
        assert result is True
        
        # Verify setting no longer exists
        assert SettingORM.get('test_key') is None

def test_delete_invalid(app):
    """Test deleting a setting with no key"""
    with app.app_context():
        # Create a setting without a key
        setting = SettingORM(value='test_value')
        
        # Try to delete
        result = setting.delete()
        
        # Verify operation failed
        assert result is False

def test_to_dict(app):
    """Test converting setting to dictionary"""
    with app.app_context():
        # Create a setting
        setting = SettingORM(key='test_key', value='test_value')
        
        # Get dictionary representation
        setting_dict = setting.to_dict()
        
        # Verify dictionary contains expected fields
        assert 'key' in setting_dict
        assert 'value' in setting_dict
        
        # Verify values are correct
        assert setting_dict['key'] == 'test_key'
        assert setting_dict['value'] == 'test_value'