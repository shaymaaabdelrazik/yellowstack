import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.scheduler_service import scheduler_service
from app.models.scheduler_orm import ScheduleORM
from app.utils.db import db
from tests.utils import create_user, create_script, create_aws_profile

@pytest.fixture
def mock_scheduler():
    """Mock the apscheduler.BackgroundScheduler instance"""
    with patch('app.services.scheduler_service.BackgroundScheduler') as mock_scheduler_class:
        # Create a mock scheduler
        mock_scheduler_instance = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler_instance
        
        # Store reference to the original scheduler
        original_scheduler = scheduler_service.scheduler
        
        # Replace with our mock
        scheduler_service.scheduler = mock_scheduler_instance
        
        yield mock_scheduler_instance
        
        # Restore original scheduler
        scheduler_service.scheduler = original_scheduler

def test_allowed_time_slots():
    """Test the allowed time slots constant"""
    assert len(scheduler_service.ALLOWED_TIME_SLOTS) == 48  # Every 30 minutes for 24 hours
    assert "00:00" in scheduler_service.ALLOWED_TIME_SLOTS
    assert "12:00" in scheduler_service.ALLOWED_TIME_SLOTS
    assert "23:30" in scheduler_service.ALLOWED_TIME_SLOTS

def test_allowed_intervals():
    """Test the allowed intervals constant"""
    # Verify some standard intervals exist
    assert "1" in scheduler_service.ALLOWED_INTERVALS
    assert "24" in scheduler_service.ALLOWED_INTERVALS
    # Ensure debug interval was removed
    assert "debug-3min" not in scheduler_service.ALLOWED_INTERVALS

def test_init_app(mock_scheduler, app):
    """Test initializing the scheduler service with a Flask app"""
    # Mock run_script function
    run_script_func = MagicMock()
    
    # Initialize with app
    scheduler_service.init_app(app, run_script_func)
    
    # Verify the scheduler was started
    mock_scheduler.start.assert_called_once()
    
    # Verify app and function were stored
    assert scheduler_service.app == app
    assert scheduler_service.run_script_func == run_script_func