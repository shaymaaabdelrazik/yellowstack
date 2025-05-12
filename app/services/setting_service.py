import logging
from app.services.setting_adapter import setting_adapter

logger = logging.getLogger('yellowstack')

class SettingService:
    """Service for managing settings using the ORM adapter"""
    
    def __init__(self, use_orm=True):
        """
        Initialize the setting service
        """
        self.setting_adapter = setting_adapter
        self.setting_adapter.use_orm = True
    
    def get_all_settings(self):
        """Get all settings as a dictionary"""
        return self.setting_adapter.get_all()
    
    def get_setting(self, key, default=None):
        """Get a setting by key with optional default value"""
        return self.setting_adapter.get(key, default)
    
    def set_setting(self, key, value):
        """Set a setting value"""
        # ORM mode is always enabled now
        return self.setting_adapter.set(key, value)
    
    def update_multiple_settings(self, settings_dict):
        """Update multiple settings at once"""
        # ORM mode is always enabled now, remove the setting if it's in the dict
        if 'USE_ORM_MODE' in settings_dict:
            settings_dict['USE_ORM_MODE'] = '1'  # Always enabled
        
        return self.setting_adapter.update_multiple(settings_dict)
    
    def delete_setting(self, key):
        """Delete a setting"""
        return self.setting_adapter.delete(key)
    
    def get_orm_mode(self):
        """Get the current ORM mode setting"""
        return True  # Always enabled now

# Create an instance using ORM mode
setting_service = SettingService()