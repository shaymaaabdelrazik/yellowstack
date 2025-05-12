import logging
from app.models import AWSProfileORM

logger = logging.getLogger('yellowstack')

class AWSProfileAdapter:
    """
    Adapter class for the SQLAlchemy ORM AWSProfile model.
    This provides a standardized interface for all AWS profile operations.
    """
    
    def __init__(self):
        """
        Initialize the adapter
        """
        self.use_orm = True  # Always True, kept for backward compatibility
    
    def get_by_id(self, profile_id):
        """Get an AWS profile by ID"""
        return AWSProfileORM.get_by_id(profile_id)
    
    def get_all(self):
        """Get all AWS profiles"""
        return AWSProfileORM.get_all()
    
    def get_default(self):
        """Get the default AWS profile"""
        return AWSProfileORM.get_default()
    
    def exists(self, name):
        """Check if an AWS profile with the given name exists"""
        return AWSProfileORM.exists(name)
    
    def create(self, name, aws_access_key, aws_secret_key, aws_region, is_default=0):
        """Create a new AWS profile"""
        # Check if the profile already exists
        orm_profile = AWSProfileORM.query.filter_by(name=name).first()
        if not orm_profile:
            orm_profile = AWSProfileORM(
                name=name,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
                aws_region=aws_region,
                is_default=is_default
            )
            profile_id = orm_profile.save()
            
            logger.debug(f"Created AWS profile {name}")
            return profile_id
        
        return orm_profile.id
    
    def update(self, profile_id, name, aws_access_key, aws_secret_key, aws_region, is_default=0):
        """Update an existing AWS profile"""
        orm_profile = AWSProfileORM.get_by_id(profile_id)
        if not orm_profile:
            return False
        
        orm_profile.name = name
        orm_profile.aws_access_key = aws_access_key
        orm_profile.aws_secret_key = aws_secret_key
        orm_profile.aws_region = aws_region
        orm_profile.is_default = is_default
        orm_profile.save()
        
        return True
    
    def delete(self, profile_id):
        """Delete an AWS profile"""
        orm_profile = AWSProfileORM.get_by_id(profile_id)
        if orm_profile:
            success = orm_profile.delete()
        else:
            success = False
        
        return success
    
    def set_as_default(self, profile_id):
        """Set a profile as the default"""
        orm_profile = AWSProfileORM.get_by_id(profile_id)
        if orm_profile:
            success = orm_profile.set_as_default()
        else:
            success = False
        
        return success

# Create a default instance that can be imported directly
aws_profile_adapter = AWSProfileAdapter()