import pytest
import json
from datetime import datetime, timedelta
from app.models.scheduler_orm import ScheduleORM
from app.models.script_orm import ScriptORM
from app.models.user_orm import UserORM
from app.models.aws_profile_orm import AWSProfileORM
from app.utils.db import db
from tests.utils import create_user, create_script, create_aws_profile

def test_schedule_creation(app):
    """Test creating a new schedule"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a new schedule
        schedule = ScheduleORM(
            script_id=script.id,
            profile_id=aws_profile.id,
            user_id=user.id,
            schedule_type='daily',
            schedule_value='12:00',
            enabled=1,
            parameters=json.dumps({'param1': 'value1'}),
            next_run=datetime.now().isoformat()
        )
        
        # Save schedule to database
        db.session.add(schedule)
        db.session.commit()
        
        # Verify schedule was created
        assert schedule.id is not None
        assert schedule.script_id == script.id
        assert schedule.profile_id == aws_profile.id
        assert schedule.user_id == user.id
        assert schedule.schedule_type == 'daily'
        assert schedule.schedule_value == '12:00'
        assert schedule.enabled == 1
        assert schedule.parameters == json.dumps({'param1': 'value1'})
        assert schedule.created_at is not None

def test_schedule_relationships(app):
    """Test schedule relationships with script, profile, and user"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a new schedule
        schedule = ScheduleORM(
            script_id=script.id,
            profile_id=aws_profile.id,
            user_id=user.id,
            schedule_type='hourly',
            schedule_value='1',
            enabled=1
        )
        
        # Save schedule to database
        db.session.add(schedule)
        db.session.commit()
        
        # Verify relationships
        assert schedule.script == script
        assert schedule.profile == aws_profile
        assert schedule.user == user
        
        # Verify bidirectional relationships
        assert schedule in script.schedules
        assert schedule in aws_profile.schedules
        assert schedule in user.schedules

def test_to_dict(app):
    """Test converting schedule to dictionary"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a schedule with all fields
        next_run = datetime.now() + timedelta(hours=1)
        next_run_str = next_run.isoformat()
        last_run = datetime.now() - timedelta(hours=1)
        last_run_str = last_run.isoformat()
        start_timestamp = datetime.now().timestamp()
        
        schedule = ScheduleORM(
            script_id=script.id,
            profile_id=aws_profile.id,
            user_id=user.id,
            schedule_type='weekly',
            schedule_value='Monday',
            enabled=1,
            parameters=json.dumps({'param1': 'value1'}),
            job_id='test-job-123',
            next_run=next_run_str,
            last_run=last_run_str,
            start_timestamp=start_timestamp
        )
        
        # Save schedule to database
        db.session.add(schedule)
        db.session.commit()
        
        # Get dictionary representation
        schedule_dict = schedule.to_dict()
        
        # Verify dictionary contains all expected fields
        assert 'id' in schedule_dict
        assert 'script_id' in schedule_dict
        assert 'profile_id' in schedule_dict
        assert 'user_id' in schedule_dict
        assert 'schedule_type' in schedule_dict
        assert 'schedule_value' in schedule_dict
        assert 'enabled' in schedule_dict
        assert 'parameters' in schedule_dict
        assert 'job_id' in schedule_dict
        assert 'next_run' in schedule_dict
        assert 'created_at' in schedule_dict
        assert 'last_run' in schedule_dict
        assert 'start_timestamp' in schedule_dict
        
        # Verify values are correct
        assert schedule_dict['script_id'] == script.id
        assert schedule_dict['profile_id'] == aws_profile.id
        assert schedule_dict['user_id'] == user.id
        assert schedule_dict['schedule_type'] == 'weekly'
        assert schedule_dict['schedule_value'] == 'Monday'
        assert schedule_dict['enabled'] == 1
        assert schedule_dict['parameters'] == json.dumps({'param1': 'value1'})
        assert schedule_dict['job_id'] == 'test-job-123'
        assert schedule_dict['next_run'] == next_run_str
        assert schedule_dict['last_run'] == last_run_str
        assert schedule_dict['start_timestamp'] == start_timestamp

def test_schedule_cascade_delete(app):
    """Test that schedules are deleted when the script is deleted (cascade)"""
    with app.app_context():
        # Create test user
        user = create_user()
        
        # Create test script
        script = create_script(user_id=user.id)
        
        # Create test AWS profile
        aws_profile = create_aws_profile(user_id=user.id)
        
        # Create a new schedule
        schedule = ScheduleORM(
            script_id=script.id,
            profile_id=aws_profile.id,
            user_id=user.id,
            schedule_type='daily',
            schedule_value='12:00',
            enabled=1
        )
        
        # Save schedule to database
        db.session.add(schedule)
        db.session.commit()
        
        # Get the schedule ID
        schedule_id = schedule.id
        
        # Delete the script
        db.session.delete(script)
        db.session.commit()
        
        # Verify the schedule was also deleted (cascade)
        deleted_schedule = db.session.get(ScheduleORM, schedule_id)
        assert deleted_schedule is None