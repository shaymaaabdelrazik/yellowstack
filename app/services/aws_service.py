import boto3
import logging
from app.services.aws_profile_adapter import aws_profile_adapter

logger = logging.getLogger('yellowstack')

class AWSService:
    """Service for managing AWS profiles and connections using the ORM adapter"""
    
    # List of AWS regions for UI/validation
    AWS_REGIONS = [
        {"id": "us-east-1", "name": "US East (N. Virginia)"},
        {"id": "us-east-2", "name": "US East (Ohio)"},
        {"id": "us-west-1", "name": "US West (N. California)"},
        {"id": "us-west-2", "name": "US West (Oregon)"},
        {"id": "af-south-1", "name": "Africa (Cape Town)"},
        {"id": "ap-east-1", "name": "Asia Pacific (Hong Kong)"},
        {"id": "ap-south-1", "name": "Asia Pacific (Mumbai)"},
        {"id": "ap-northeast-1", "name": "Asia Pacific (Tokyo)"},
        {"id": "ap-northeast-2", "name": "Asia Pacific (Seoul)"},
        {"id": "ap-northeast-3", "name": "Asia Pacific (Osaka)"},
        {"id": "ap-southeast-1", "name": "Asia Pacific (Singapore)"},
        {"id": "ap-southeast-2", "name": "Asia Pacific (Sydney)"},
        {"id": "ap-southeast-3", "name": "Asia Pacific (Jakarta)"},
        {"id": "ca-central-1", "name": "Canada (Central)"},
        {"id": "eu-central-1", "name": "Europe (Frankfurt)"},
        {"id": "eu-west-1", "name": "Europe (Ireland)"},
        {"id": "eu-west-2", "name": "Europe (London)"},
        {"id": "eu-west-3", "name": "Europe (Paris)"},
        {"id": "eu-north-1", "name": "Europe (Stockholm)"},
        {"id": "eu-south-1", "name": "Europe (Milan)"},
        {"id": "me-south-1", "name": "Middle East (Bahrain)"},
        {"id": "sa-east-1", "name": "South America (São Paulo)"}
    ]
    
    def __init__(self, use_orm=True):
        """
        Initialize the AWS service
        """
        self.aws_profile_adapter = aws_profile_adapter
        self.aws_profile_adapter.use_orm = True
    
    def get_all_profiles(self):
        """Get all AWS profiles"""
        return self.aws_profile_adapter.get_all()
    
    def get_profile_by_id(self, profile_id):
        """Get an AWS profile by ID"""
        return self.aws_profile_adapter.get_by_id(profile_id)
    
    def get_default_profile(self):
        """Get the default AWS profile"""
        return self.aws_profile_adapter.get_default()
    
    def create_profile(self, name, aws_access_key, aws_secret_key, aws_region, is_default=False):
        """Create a new AWS profile"""
        # Validate inputs
        if not name or not aws_access_key or not aws_secret_key or not aws_region:
            raise ValueError("All profile fields are required")
        
        # Check if profile exists
        if self.aws_profile_adapter.exists(name):
            raise ValueError(f"A profile with the name '{name}' already exists")
        
        # Validate AWS credentials
        try:
            self._validate_aws_credentials(aws_access_key, aws_secret_key, aws_region)
        except Exception as e:
            raise ValueError(f"Invalid AWS credentials: {str(e)}")
        
        # Create profile
        profile_id = self.aws_profile_adapter.create(
            name=name,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            aws_region=aws_region,
            is_default=1 if is_default else 0
        )
        
        logger.info(f"AWS profile created: {name} (ID: {profile_id})")
        return profile_id
    
    def update_profile(self, profile_id, name=None, aws_access_key=None, aws_secret_key=None, 
                        aws_region=None, is_default=None):
        """Update an AWS profile"""
        profile = self.aws_profile_adapter.get_by_id(profile_id)
        
        if not profile:
            raise ValueError(f"Profile with ID {profile_id} not found")
        
        # Get current values if not provided
        if name is None:
            name = profile.name
            
        if aws_access_key is None:
            aws_access_key = profile.aws_access_key
            
        if aws_secret_key is None:
            aws_secret_key = profile.aws_secret_key
            
        if aws_region is None:
            aws_region = profile.aws_region
            
        if is_default is None:
            is_default = profile.is_default
        
        # Validate credentials if any of the AWS fields changed
        if aws_access_key != profile.aws_access_key or aws_secret_key != profile.aws_secret_key or aws_region != profile.aws_region:
            try:
                self._validate_aws_credentials(aws_access_key, aws_secret_key, aws_region)
            except Exception as e:
                raise ValueError(f"Invalid AWS credentials: {str(e)}")
        
        # Update the profile
        success = self.aws_profile_adapter.update(
            profile_id=profile_id,
            name=name,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            aws_region=aws_region,
            is_default=1 if is_default else 0
        )
        
        if success:
            logger.info(f"AWS profile updated: {name} (ID: {profile_id})")
        
        return success
    
    def delete_profile(self, profile_id):
        """Delete an AWS profile"""
        profile = self.aws_profile_adapter.get_by_id(profile_id)

        if not profile:
            raise ValueError(f"Profile with ID {profile_id} not found")

        # Try to delete the profile
        success = self.aws_profile_adapter.delete(profile_id)

        if success:
            logger.info(f"AWS profile deleted: {profile.name} (ID: {profile_id})")
        else:
            logger.warning(f"AWS profile deletion failed, profile is in use: {profile.name} (ID: {profile_id})")
            raise ValueError("This profile is in use by active schedulers and cannot be deleted. Please disable the schedulers first.")

        return success
    
    def set_default_profile(self, profile_id):
        """Set an AWS profile as the default"""
        profile = self.aws_profile_adapter.get_by_id(profile_id)
        
        if not profile:
            raise ValueError(f"Profile with ID {profile_id} not found")
        
        success = self.aws_profile_adapter.set_as_default(profile_id)
        
        if success:
            logger.info(f"AWS profile set as default: {profile.name} (ID: {profile_id})")
        
        return success
    
    def get_boto3_session(self, profile_id=None):
        """Get a boto3 session for a profile"""
        # If no profile_id is provided, use the default
        if profile_id is None:
            profile = self.aws_profile_adapter.get_default()
            if not profile:
                raise ValueError("No AWS profiles found")
        else:
            profile = self.aws_profile_adapter.get_by_id(profile_id)
            if not profile:
                raise ValueError(f"Profile with ID {profile_id} not found")
        
        # Create and return the session
        return boto3.Session(
            aws_access_key_id=profile.aws_access_key,
            aws_secret_access_key=profile.aws_secret_key,
            region_name=profile.aws_region
        )
    
    def get_aws_client(self, service, profile_id=None):
        """Get a boto3 client for a service"""
        session = self.get_boto3_session(profile_id)
        return session.client(service)
    
    def get_aws_resource(self, service, profile_id=None):
        """Get a boto3 resource for a service"""
        session = self.get_boto3_session(profile_id)
        return session.resource(service)
    
    def _validate_aws_credentials(self, access_key, secret_key, region):
        """Validate AWS credentials by calling the STS service"""
        try:
            boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            ).get_caller_identity()
            return True
        except Exception as e:
            logger.error(f"AWS credential validation failed: {str(e)}")
            raise e

# Create an instance using ORM mode
aws_service = AWSService()