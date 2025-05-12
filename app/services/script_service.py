import os
import importlib.util
import json
import logging
from app.services.script_adapter import script_adapter

logger = logging.getLogger('yellowstack')

class ScriptService:
    """Service for managing scripts using the ORM adapter"""
    
    def __init__(self, use_orm=True):
        """
        Initialize the script service
        """
        self.script_adapter = script_adapter
        self.script_adapter.use_orm = True
    
    def get_all_scripts(self):
        """Get all registered scripts"""
        return self.script_adapter.get_all()
    
    def get_script_by_id(self, script_id):
        """Get a script by ID"""
        return self.script_adapter.get_by_id(script_id)
    
    def create_script(self, name, description, path, parameters=None, user_id=None):
        """Create a new script"""
        # Check if script exists
        if self.script_adapter.exists(name):
            raise ValueError(f"A script with the name '{name}' already exists")
        
        # Validate script path
        self._validate_script_path(path)
        
        # Create and save script
        script_id = self.script_adapter.create(
            name=name,
            description=description,
            path=path,
            parameters=parameters,
            user_id=user_id
        )
        
        logger.info(f"Script created: {name} (ID: {script_id})")
        return script_id
    
    def update_script(self, script_id, name=None, description=None, path=None, parameters=None):
        """Update an existing script"""
        script = self.script_adapter.get_by_id(script_id)
        
        if not script:
            raise ValueError(f"Script with ID {script_id} not found")
        
        # Get current values if new ones not provided
        if name is None:
            name = script.name
            
        if description is None:
            description = script.description
            
        if path is None:
            path = script.path
        else:
            # Validate the new path
            self._validate_script_path(path)
            
        if parameters is None:
            parameters = script.parameters
        
        # Update the script
        success = self.script_adapter.update(
            script_id=script_id,
            name=name,
            description=description,
            path=path,
            parameters=parameters,
            user_id=script.user_id
        )
        
        if success:
            logger.info(f"Script updated: {name} (ID: {script_id})")
        else:
            logger.warning(f"Script update failed: {name} (ID: {script_id})")
            
        return success
    
    def delete_script(self, script_id):
        """Delete a script"""
        script = self.script_adapter.get_by_id(script_id)
        
        if not script:
            raise ValueError(f"Script with ID {script_id} not found")
        
        # Delete the script
        success = self.script_adapter.delete(script_id)
        
        if success:
            logger.info(f"Script deleted: {script.name} (ID: {script_id})")
        else:
            logger.warning(f"Script deletion failed, script has execution history: {script.name} (ID: {script_id})")
            
        return success
    
    def _validate_script_path(self, path):
        """Validate a script path"""
        if not os.path.exists(path):
            raise ValueError(f"Script path not found: {path}")
        
        if not path.endswith('.py'):
            raise ValueError("Script must be a Python file (.py)")
        
        # Try to import the script to check if it's valid
        try:
            spec = importlib.util.spec_from_file_location("script_module", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ValueError(f"Script could not be imported: {str(e)}")
        
        return True
    
    def parse_script_parameters(self, parameters_json):
        """Parse script parameters from JSON string"""
        if not parameters_json:
            return []
            
        try:
            return json.loads(parameters_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing script parameters: {str(e)}")
            return []
    
    def collect_script_parameters(self, parameters_form_data):
        """Collect script parameters from form data"""
        params = []
        
        # Form data is expected to be in the format:
        # param-name-1: name1, param-default-1: default1, etc.
        param_names = [key for key in parameters_form_data if key.startswith('param-name-')]
        
        for key in sorted(param_names):
            index = key.split('-')[-1]
            name = parameters_form_data.get(f'param-name-{index}')
            default = parameters_form_data.get(f'param-default-{index}', '')
            
            if name:
                params.append({
                    'name': name,
                    'default': default
                })
        
        return params

# Create an instance using ORM mode
script_service = ScriptService()