import logging
from datetime import datetime
from app.models import ExecutionORM
from app.utils.db import db

logger = logging.getLogger('yellowstack')

class ExecutionAdapter:
    """
    Adapter class for the SQLAlchemy ORM Execution model.
    This provides a standardized interface for all execution operations.
    """
    
    def __init__(self):
        """
        Initialize the adapter
        """
        self.use_orm = True  # Always True, kept for backward compatibility
    
    def get_by_id(self, execution_id):
        """Get an execution by ID"""
        return ExecutionORM.get_by_id(execution_id)
        
    def get_by_id_with_details(self, execution_id):
        """Get an execution by ID with related data as dictionary"""
        return ExecutionORM.get_by_id_with_details(execution_id)
    
    def get_recent(self, limit=10):
        """Get recent executions"""
        return ExecutionORM.get_recent(limit)
    
    def get_history(self, page=1, per_page=10, filters=None):
        """Get execution history with pagination and filters"""
        return ExecutionORM.get_history(page, per_page, filters)
    
    def get_stats(self, days=7):
        """Get execution statistics for the dashboard chart"""
        return ExecutionORM.get_stats(days)
    
    def create(self, script_id, aws_profile_id, user_id, status="Pending", 
               start_time=None, parameters=None, is_scheduled=0):
        """Create a new execution record"""
        # Set default start time if not provided
        if start_time is None:
            start_time = datetime.now().isoformat()
        
        # Create execution using ORM
        orm_execution = ExecutionORM(
            script_id=script_id,
            aws_profile_id=aws_profile_id,
            user_id=user_id,
            status=status,
            start_time=start_time,
            parameters=parameters,
            is_scheduled=is_scheduled
        )
        execution_id = orm_execution.save()
        
        logger.debug(f"Created execution for script ID {script_id}")
        return execution_id
    
    def update_status(self, execution_id, status, output=None):
        """Update the status of an execution"""
        orm_execution = ExecutionORM.get_by_id(execution_id)
        if orm_execution:
            # Make sure we have an ORM object, not a dict
            if isinstance(orm_execution, dict):
                # Fetch the actual ORM object
                orm_execution = db.session.get(ExecutionORM, execution_id)
                
            if orm_execution:
                orm_execution.update_status(status, output)
                return True
        
        return False
    
    def append_output(self, execution_id, output):
        """Append output to an execution"""
        orm_execution = ExecutionORM.get_by_id(execution_id)
        if orm_execution:
            # Make sure we have an ORM object, not a dict
            if isinstance(orm_execution, dict):
                # Fetch the actual ORM object
                orm_execution = db.session.get(ExecutionORM, execution_id)
                
            if orm_execution:
                orm_execution.append_output(output)
                return True
        
        return False
    
    def update_ai_analysis(self, execution_id, analysis, solution):
        """Update AI analysis for an execution"""
        orm_execution = ExecutionORM.get_by_id(execution_id)
        if orm_execution:
            # Make sure we have an ORM object, not a dict
            if isinstance(orm_execution, dict):
                # Fetch the actual ORM object
                orm_execution = db.session.get(ExecutionORM, execution_id)
                
            if orm_execution:
                orm_execution.update_ai_analysis(analysis, solution)
                return True
        
        return False
    
    def cancel(self, execution_id):
        """Cancel an execution"""
        orm_execution = ExecutionORM.get_by_id(execution_id)
        if orm_execution:
            # Make sure we have an ORM object, not a dict
            if isinstance(orm_execution, dict):
                # Fetch the actual ORM object
                orm_execution = db.session.get(ExecutionORM, execution_id)
                
            if orm_execution:
                return orm_execution.cancel()
        
        return False
    
    def parse_parameters(self, execution):
        """Parse parameters from an execution"""
        # Handle case when we are passed an execution instance
        if isinstance(execution, ExecutionORM):
            return execution.parse_parameters()
        
        # Otherwise look up by ID
        if isinstance(execution, int):
            execution_obj = self.get_by_id(execution)
            if not execution_obj:
                return {}
            
            return execution_obj.parse_parameters()
                
        return {}

# Create a default instance that can be imported directly
execution_adapter = ExecutionAdapter()