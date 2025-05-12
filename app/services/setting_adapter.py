import logging
from app.models import SettingORM

logger = logging.getLogger('yellowstack')

class SettingAdapter:
    """
    Adapter class for the SQLAlchemy ORM Setting model.
    This provides a standardized interface for all setting operations.
    """
    
    def __init__(self):
        """
        Initialize the adapter
        """
        self.use_orm = True  # Always True, kept for backward compatibility
    
    def get(self, key, default=None):
        """Get a setting by key with optional default value"""
        return SettingORM.get(key, default)
    
    def get_all(self):
        """Get all settings as a dictionary"""
        return SettingORM.get_all()
    
    def set(self, key, value):
        """Set a setting value"""
        return SettingORM.set(key, value)
    
    def update_multiple(self, settings_dict):
        """Update multiple settings at once"""
        if not settings_dict:
            return False
        
        return SettingORM.update_multiple(settings_dict)
    
    def delete(self, key):
        """Delete a setting"""
        orm_setting = SettingORM.query.filter_by(key=key).first()
        if orm_setting:
            success = orm_setting.delete()
        else:
            success = True  # Not an error if it doesn't exist
        
        return success

# Create a default instance that can be imported directly
setting_adapter = SettingAdapter()