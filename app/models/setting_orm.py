from app.utils.db import db

class SettingORM(db.Model):
    """SQLAlchemy ORM model for settings table"""
    
    __tablename__ = 'settings'
    
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    
    def __init__(self, key=None, value=None):
        """Initialize a new setting"""
        self.key = key
        self.value = value
    
    @classmethod
    def get_by_key(cls, key):
        """Get a setting object by key"""
        return cls.query.filter_by(key=key).first()
        
    @classmethod
    def get(cls, key, default=None):
        """Get a setting value by key with optional default value"""
        setting = cls.query.filter_by(key=key).first()
        
        if setting:
            return setting.value
        return default
    
    @classmethod
    def get_all(cls):
        """Get all settings as a dictionary"""
        settings_rows = cls.query.all()
        
        settings = {}
        for row in settings_rows:
            settings[row.key] = row.value
        
        return settings
    
    @classmethod
    def set(cls, key, value):
        """Set a setting value"""
        setting = cls.query.filter_by(key=key).first()
        
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
            
        db.session.commit()
        return True
    
    @classmethod
    def update_multiple(cls, settings_dict):
        """Update multiple settings at once"""
        if not settings_dict:
            return False
        
        for key, value in settings_dict.items():
            setting = cls.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
            else:
                setting = cls(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        return True
    
    def save(self):
        """Save the setting to the database"""
        if not self.key:
            return False
            
        db.session.add(self)
        db.session.commit()
        return True
    
    def delete(self):
        """Delete the setting from the database"""
        if not self.key:
            return False
            
        db.session.delete(self)
        db.session.commit()
        return True
    
    def to_dict(self):
        """Convert Setting object to dictionary"""
        return {
            'key': self.key,
            'value': self.value
        }