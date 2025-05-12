import pytest
from app.models.aws_profile_orm import AWSProfileORM
from app.models.execution_orm import ExecutionORM
from app.utils.db import db
from tests.utils import create_user, create_script, create_aws_profile

def test_aws_profile_creation(app):
    """Test creating a new AWS profile"""
    with app.app_context():
        # Create a new AWS profile
        aws_profile = AWSProfileORM(
            name='Test Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2',
            is_default=1
        )
        
        # Save profile to database
        aws_profile_id = aws_profile.save()
        
        # Verify profile was created
        assert aws_profile_id is not None
        assert aws_profile.id is not None
        assert aws_profile.name == 'Test Profile'
        assert aws_profile.aws_access_key == 'AKIATEST12345'
        assert aws_profile.aws_secret_key == 'testsecretkey12345'
        assert aws_profile.aws_region == 'us-west-2'
        assert aws_profile.is_default == 1

def test_get_by_id(app):
    """Test retrieving an AWS profile by ID"""
    with app.app_context():
        # Create test AWS profile
        aws_profile = AWSProfileORM(
            name='Test Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        aws_profile_id = aws_profile.save()
        
        # Retrieve profile by ID
        retrieved_profile = AWSProfileORM.get_by_id(aws_profile_id)
        
        # Verify profile was retrieved correctly
        assert retrieved_profile is not None
        assert retrieved_profile.id == aws_profile_id
        assert retrieved_profile.name == 'Test Profile'
        assert retrieved_profile.aws_access_key == 'AKIATEST12345'
        assert retrieved_profile.aws_secret_key == 'testsecretkey12345'
        assert retrieved_profile.aws_region == 'us-west-2'

def test_get_by_id_not_found(app):
    """Test retrieving a non-existent AWS profile"""
    with app.app_context():
        # Try to retrieve a profile with a non-existent ID
        profile = AWSProfileORM.get_by_id(999)
        
        # Verify no profile was found
        assert profile is None

def test_get_all(app):
    """Test retrieving all AWS profiles"""
    with app.app_context():
        # Create test profiles
        profile1 = AWSProfileORM(
            name='Profile 1',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        profile1.save()
        
        profile2 = AWSProfileORM(
            name='Profile 2',
            aws_access_key='AKIATEST67890',
            aws_secret_key='testsecretkey67890',
            aws_region='us-east-1'
        )
        profile2.save()
        
        # Retrieve all profiles
        profiles = AWSProfileORM.get_all()
        
        # Verify profiles were retrieved correctly
        assert len(profiles) == 2
        
        # Get profile names
        profile_names = [profile.get('name') for profile in profiles]
        assert 'Profile 1' in profile_names
        assert 'Profile 2' in profile_names

def test_get_default(app):
    """Test retrieving the default AWS profile"""
    with app.app_context():
        # Create test profiles
        # First one should be automatically set as default
        profile1 = AWSProfileORM(
            name='Profile 1',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        profile1.save()
        
        # This one has is_default=1, should become the new default
        profile2 = AWSProfileORM(
            name='Profile 2',
            aws_access_key='AKIATEST67890',
            aws_secret_key='testsecretkey67890',
            aws_region='us-east-1',
            is_default=1
        )
        profile2.save()
        
        # Get the default profile
        default_profile = AWSProfileORM.get_default()
        
        # Verify default profile is correct
        assert default_profile is not None
        assert default_profile.name == 'Profile 2'
        
        # Verify in database
        profile1_db = AWSProfileORM.get_by_id(profile1.id)
        assert profile1_db.is_default == 0
        
        profile2_db = AWSProfileORM.get_by_id(profile2.id)
        assert profile2_db.is_default == 1

def test_get_default_with_no_profiles(app):
    """Test retrieving default profile when no profiles exist"""
    with app.app_context():
        # Delete any existing profiles
        AWSProfileORM.query.delete()
        db.session.commit()
        
        # Get the default profile
        default_profile = AWSProfileORM.get_default()
        
        # Verify no default profile was found
        assert default_profile is None

def test_first_profile_becomes_default(app):
    """Test that the first profile is automatically set as default"""
    with app.app_context():
        # Delete any existing profiles
        AWSProfileORM.query.delete()
        db.session.commit()
        
        # Create a profile without specifying is_default
        profile = AWSProfileORM(
            name='Only Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        profile.save()
        
        # Verify it became default
        default_profile = AWSProfileORM.get_default()
        assert default_profile is not None
        assert default_profile.id == profile.id
        assert default_profile.is_default == 1

def test_save_update(app):
    """Test updating an existing AWS profile"""
    with app.app_context():
        # Create and save a profile
        profile = AWSProfileORM(
            name='Test Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        profile_id = profile.save()
        
        # Update the profile
        profile.name = 'Updated Profile'
        profile.aws_region = 'eu-west-1'
        profile.save()
        
        # Verify profile was updated
        updated_profile = AWSProfileORM.get_by_id(profile_id)
        assert updated_profile.name == 'Updated Profile'
        assert updated_profile.aws_region == 'eu-west-1'

def test_set_as_default(app):
    """Test setting a profile as default"""
    with app.app_context():
        # Create test profiles
        profile1 = AWSProfileORM(
            name='Profile 1',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2',
            is_default=1
        )
        profile1.save()
        
        profile2 = AWSProfileORM(
            name='Profile 2',
            aws_access_key='AKIATEST67890',
            aws_secret_key='testsecretkey67890',
            aws_region='us-east-1',
            is_default=0
        )
        profile2.save()
        
        # Verify profile1 is default
        assert profile1.is_default == 1
        assert profile2.is_default == 0
        
        # Set profile2 as default
        result = profile2.set_as_default()
        
        # Verify operation was successful
        assert result is True
        
        # Verify in database
        profile1_db = AWSProfileORM.get_by_id(profile1.id)
        assert profile1_db.is_default == 0
        
        profile2_db = AWSProfileORM.get_by_id(profile2.id)
        assert profile2_db.is_default == 1

def test_delete_unused_profile(app):
    """Test deleting an AWS profile that is not used by any executions"""
    with app.app_context():
        # Create test profiles
        profile1 = AWSProfileORM(
            name='Profile 1',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2',
            is_default=1
        )
        profile1.save()
        
        profile2 = AWSProfileORM(
            name='Profile 2',
            aws_access_key='AKIATEST67890',
            aws_secret_key='testsecretkey67890',
            aws_region='us-east-1',
            is_default=0
        )
        profile2.save()
        
        # Verify profile2 exists
        assert AWSProfileORM.get_by_id(profile2.id) is not None
        
        # Delete profile2
        result = profile2.delete()
        
        # Verify deletion was successful
        assert result is True
        
        # Verify profile2 no longer exists
        assert AWSProfileORM.get_by_id(profile2.id) is None

def test_delete_default_profile_changes_default(app):
    """Test that deleting the default profile sets another as default"""
    with app.app_context():
        # Create test profiles
        profile1 = AWSProfileORM(
            name='Profile 1',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2',
            is_default=1
        )
        profile1.save()
        
        profile2 = AWSProfileORM(
            name='Profile 2',
            aws_access_key='AKIATEST67890',
            aws_secret_key='testsecretkey67890',
            aws_region='us-east-1',
            is_default=0
        )
        profile2.save()
        
        # Delete the default profile
        result = profile1.delete()
        
        # Verify deletion was successful
        assert result is True
        
        # Verify profile2 became the default
        profile2_db = AWSProfileORM.get_by_id(profile2.id)
        assert profile2_db.is_default == 1

def test_delete_profile_in_use(app):
    """Test that a profile used by executions cannot be deleted"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create an execution using the profile
        execution = ExecutionORM(
            script_id=script.id,
            aws_profile_id=aws_profile.id,
            user_id=user.id,
            status="Success"
        )
        execution.save()
        
        # Try to delete the profile
        result = aws_profile.delete()
        
        # Verify deletion failed
        assert result is False
        
        # Verify profile still exists
        assert AWSProfileORM.get_by_id(aws_profile.id) is not None

def test_exists(app):
    """Test checking if a profile name exists"""
    with app.app_context():
        # Create a profile
        profile = AWSProfileORM(
            name='Test Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2'
        )
        profile.save()
        
        # Check existing profile name
        assert AWSProfileORM.exists('Test Profile') is True
        
        # Check non-existent profile name
        assert AWSProfileORM.exists('Nonexistent Profile') is False

def test_to_dict(app):
    """Test converting AWS profile to dictionary"""
    with app.app_context():
        # Create a profile
        profile = AWSProfileORM(
            name='Test Profile',
            aws_access_key='AKIATEST12345',
            aws_secret_key='testsecretkey12345',
            aws_region='us-west-2',
            is_default=1
        )
        profile.save()
        
        # Get dictionary representation
        profile_dict = profile.to_dict()
        
        # Verify dictionary contains expected fields
        assert 'id' in profile_dict
        assert 'name' in profile_dict
        assert 'aws_access_key' in profile_dict
        assert 'aws_secret_key' in profile_dict
        assert 'aws_region' in profile_dict
        assert 'is_default' in profile_dict
        
        # Verify values are correct
        assert profile_dict['name'] == 'Test Profile'
        assert profile_dict['aws_access_key'] == 'AKIATEST12345'
        assert profile_dict['aws_secret_key'] == 'testsecretkey12345'
        assert profile_dict['aws_region'] == 'us-west-2'
        assert profile_dict['is_default'] == 1