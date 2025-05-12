from app.utils.db import db

class AWSProfileORM(db.Model):
    """SQLAlchemy ORM model for AWS profiles table"""
    
    __tablename__ = 'aws_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    aws_access_key = db.Column(db.String(255), nullable=False)
    aws_secret_key = db.Column(db.String(255), nullable=False)
    aws_region = db.Column(db.String(50), nullable=False)
    is_default = db.Column(db.Integer, default=0)
    
    # Define relationship with Execution model (will be defined later)
    executions = db.relationship('ExecutionORM', backref='aws_profile', lazy=True)
    
    def __init__(self, name=None, aws_access_key=None, aws_secret_key=None, 
                 aws_region=None, is_default=0):
        """Initialize a new AWS profile"""
        self.name = name
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.aws_region = aws_region
        self.is_default = is_default
    
    @classmethod
    def get_by_id(cls, profile_id):
        """Get an AWS profile by ID"""
        return db.session.get(cls, profile_id)
    
    @classmethod
    def get_all(cls):
        """Get all AWS profiles"""
        profiles = cls.query.all()
        return [profile.to_dict() for profile in profiles]
    
    @classmethod
    def get_default(cls):
        """Get the default AWS profile"""
        # Try to get the default profile
        profile = cls.query.filter_by(is_default=1).first()
        
        # If no default profile, get the first one
        if not profile:
            profile = cls.query.order_by(cls.id).first()
            
        return profile
    
    def save(self):
        """Save the AWS profile to the database"""
        # If this is the default profile, unset all other profiles
        if self.is_default:
            AWSProfileORM.query.update({AWSProfileORM.is_default: 0})
        
        db.session.add(self)
        db.session.commit()
        
        # If this was the only profile, make it the default
        if AWSProfileORM.query.count() == 1:
            self.is_default = 1
            db.session.commit()
        
        return self.id
    
    def delete(self):
        """Delete the AWS profile from the database"""
        if not self.id:
            return False

        # Check if profile is in use by any active schedulers
        from app.models.scheduler_orm import ScheduleORM
        in_use_by_active_scheduler = ScheduleORM.query.filter_by(profile_id=self.id, enabled=1).first() is not None

        if in_use_by_active_scheduler:
            return False

        # Get the default profile to use as replacement
        default_profile = AWSProfileORM.query.filter_by(is_default=1).first()
        
        # If no default profile exists, pick the first profile that isn't the one being deleted
        if not default_profile or default_profile.id == self.id:
            default_profile = AWSProfileORM.query.filter(AWSProfileORM.id != self.id).first()
        
        # If there's no other profile at all, we can't delete this one
        if not default_profile:
            return False

        # Check for inactive schedulers and update them to use the default profile
        inactive_schedulers = ScheduleORM.query.filter_by(profile_id=self.id, enabled=0).all()
        for scheduler in inactive_schedulers:
            scheduler.profile_id = default_profile.id
        
        # Check for executions and update them to use the default profile
        from app.models.execution_orm import ExecutionORM
        executions_using_profile = ExecutionORM.query.filter_by(aws_profile_id=self.id).all()
        for execution in executions_using_profile:
            execution.aws_profile_id = default_profile.id
        
        # Commit changes to reassigned relationships
        if inactive_schedulers or executions_using_profile:
            db.session.commit()

        # Remember if it was the default
        was_default = self.is_default

        # Delete profile
        db.session.delete(self)
        db.session.commit()

        # If it was the default, set another one as default
        if was_default:
            other_profile = AWSProfileORM.query.first()
            if other_profile:
                other_profile.is_default = 1
                db.session.commit()

        return True
    
    def set_as_default(self):
        """Set this profile as the default"""
        if not self.id:
            return False
        
        # Unset all profiles
        AWSProfileORM.query.update({AWSProfileORM.is_default: 0})
        
        # Set this one as default
        self.is_default = 1
        db.session.commit()
        
        return True
    
    @classmethod
    def exists(cls, name):
        """Check if an AWS profile with the given name exists"""
        return cls.query.filter_by(name=name).first() is not None
    
    def to_dict(self):
        """Convert AWSProfile object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'aws_access_key': self.aws_access_key,
            'aws_secret_key': self.aws_secret_key,
            'aws_region': self.aws_region,
            'is_default': self.is_default
        }