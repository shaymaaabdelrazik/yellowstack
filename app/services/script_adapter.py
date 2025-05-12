import logging
from app.models import ScriptORM

logger = logging.getLogger('yellowstack')

class ScriptAdapter:
    """
    Adapter class for the SQLAlchemy ORM Script model.
    This provides a standardized interface for all script operations.
    """
    
    def __init__(self):
        """
        Initialize the adapter
        """
        self.use_orm = True  # Always True, kept for backward compatibility
    
    def get_by_id(self, script_id):
        """Get a script by ID"""
        return ScriptORM.get_by_id(script_id)
    
    def get_all(self):
        """Get all scripts"""
        return ScriptORM.get_all()
    
    def exists(self, name):
        """Check if a script with the given name exists"""
        return ScriptORM.exists(name)
    
    def create(self, name, description, path, parameters=None, user_id=None):
        """Create a new script"""
        # Check if the script already exists
        orm_script = ScriptORM.query.filter_by(name=name).first()
        if not orm_script:
            orm_script = ScriptORM(
                name=name,
                description=description,
                path=path,
                parameters=parameters,
                user_id=user_id
            )
            script_id = orm_script.save()
            
            logger.debug(f"Created script {name}")
            return script_id
        
        return orm_script.id
    
    def update(self, script_id, name, description, path, parameters=None, user_id=None):
        """Update an existing script"""
        orm_script = ScriptORM.get_by_id(script_id)
        if not orm_script:
            return False
        
        orm_script.name = name
        orm_script.description = description
        orm_script.path = path
        orm_script.parameters = parameters
        orm_script.user_id = user_id
        orm_script.save()
        
        return True
    
    def delete(self, script_id):
        """Delete a script"""
        orm_script = ScriptORM.get_by_id(script_id)
        if orm_script:
            success = orm_script.delete()
        else:
            success = False
        
        return success
    
    def parse_parameters(self, script):
        """Parse parameters from a script model"""
        # If we're passed a script instance
        if isinstance(script, ScriptORM):
            return script.parse_parameters()
        
        # Otherwise, look up the script by ID
        script_obj = self.get_by_id(script)
        if script_obj:
            return script_obj.parse_parameters()
        
        return []

# Create a default instance that can be imported directly
script_adapter = ScriptAdapter()