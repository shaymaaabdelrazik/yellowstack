import json
from app.utils.db import db

class ScriptORM(db.Model):
    """SQLAlchemy ORM model for scripts table"""
    
    __tablename__ = 'scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    path = db.Column(db.String(255), nullable=False)
    parameters = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Define relationship with User model
    user = db.relationship('UserORM', backref=db.backref('scripts', lazy=True))
    
    def __init__(self, name=None, description=None, path=None, parameters=None, user_id=None):
        """Initialize a new script"""
        self.name = name
        self.description = description
        self.path = path
        self.parameters = parameters
        self.user_id = user_id
    
    @classmethod
    def get_by_id(cls, script_id):
        """Get a script by ID"""
        return db.session.get(cls, script_id)
    
    @classmethod
    def get_all(cls):
        """Get all scripts"""
        scripts = cls.query.all()
        result = []
        
        for script in scripts:
            script_dict = script.to_dict()
            
            # Add username if available
            if script.user:
                script_dict['username'] = script.user.username
            else:
                script_dict['username'] = None
                
            result.append(script_dict)
            
        return result
    
    def save(self):
        """Save the script to the database"""
        db.session.add(self)
        db.session.commit()
        return self.id
    
    def delete(self):
        """Delete the script from the database"""
        if not self.id:
            return False
            
        db.session.delete(self)
        db.session.commit()
        return True
    
    @classmethod
    def exists(cls, name):
        """Check if a script with the given name exists"""
        return cls.query.filter_by(name=name).first() is not None
    
    def to_dict(self):
        """Convert Script object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'parameters': self.parameters,
            'user_id': self.user_id
        }
    
    def parse_parameters(self):
        """Parse the parameters JSON string to a Python object"""
        if not self.parameters:
            return []
            
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return []