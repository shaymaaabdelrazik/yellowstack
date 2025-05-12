import json
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app
from app.services import execution_service
from app.utils.db import db
from app.models.script_orm import ScriptORM
from app.models.aws_profile_orm import AWSProfileORM

logger = logging.getLogger('yellowstack')

class SchedulerService:
    """Service for managing scheduled script executions using the ORM"""
    
    # Allowed time and interval values for UI/validation
    ALLOWED_TIME_SLOTS = [
        "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", 
        "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", 
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", 
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", 
        "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
    ]
    
    # Standard hours-based intervals
    ALLOWED_INTERVALS = ["1", "2", "3", "4", "6", "8", "12", "24"]
    
    def __init__(self, use_orm=True):
        """Initialize the scheduler manager"""
        self.scheduler = BackgroundScheduler()
        self.run_script_func = None
        self.app = None
        self.execution_service = execution_service
        self.execution_service.use_orm = True
    
    def init_app(self, app, run_script_func):
        """Initialize with Flask app and run_script function"""
        self.app = app
        self.run_script_func = run_script_func
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("ORM Scheduler initialized and started")
        
        # Load existing schedules
        self.load_schedules()
    
    def load_schedules(self):
        """Load and restore all enabled schedules from the database"""
        if not self.app:
            logger.error("Cannot load schedules: app not initialized")
            return
            
        with self.app.app_context():
            try:
                # Import the model here to avoid circular imports
                from app.models.scheduler_orm import ScheduleORM
                
                # Get all enabled schedules
                schedules = ScheduleORM.query.filter_by(enabled=1).all()
                
                logger.info(f"Found {len(schedules)} active schedules to load")
                
                # Restore all active jobs
                restored = 0
                for schedule in schedules:
                    try:
                        job = self._add_job(
                            schedule.id,
                            schedule.script_id,
                            schedule.profile_id,
                            schedule.user_id,
                            schedule.schedule_type,
                            schedule.schedule_value,
                            json.loads(schedule.parameters) if schedule.parameters else {}
                        )
                        if job:
                            restored += 1
                    except Exception as e:
                        logger.error(f"Error restoring schedule {schedule.id}: {str(e)}")
                
                logger.info(f"Successfully restored {restored} of {len(schedules)} schedules from database")
            except Exception as e:
                logger.error(f"Error loading schedules: {str(e)}", exc_info=True)
    
    def get_schedules(self, include_disabled=False):
        """Get all schedules"""
        with self.app.app_context():
            # Import the model here to avoid circular imports
            from app.models.scheduler_orm import ScheduleORM
            from app.models.user_orm import UserORM
            
            # Build query with joins
            query = db.session.query(
                ScheduleORM,
                ScriptORM.name.label('script_name'),
                AWSProfileORM.name.label('profile_name'),
                UserORM.username
            ).join(
                ScriptORM, ScheduleORM.script_id == ScriptORM.id
            ).join(
                AWSProfileORM, ScheduleORM.profile_id == AWSProfileORM.id
            ).join(
                UserORM, ScheduleORM.user_id == UserORM.id
            )
            
            # Filter disabled schedules if requested
            if not include_disabled:
                query = query.filter(ScheduleORM.enabled == 1)
            
            # Order by created_at
            query = query.order_by(ScheduleORM.created_at.desc())
            
            # Execute query
            results = query.all()
            
            # Process results
            schedules = []
            for row in results:
                schedule = row[0].to_dict()  # Get Schedule object and convert to dict
                schedule['script_name'] = row.script_name
                schedule['profile_name'] = row.profile_name
                schedule['username'] = row.username
                
                # Format parameters for each schedule
                if schedule['parameters']:
                    try:
                        schedule['parameters'] = json.loads(schedule['parameters'])
                    except:
                        schedule['parameters'] = {}
                
                schedules.append(schedule)
            
            return schedules
    
    def get_schedule(self, schedule_id):
        """Get a specific schedule"""
        with self.app.app_context():
            # Import the model here to avoid circular imports
            from app.models.scheduler_orm import ScheduleORM
            from app.models.user_orm import UserORM
            
            # Build query with joins
            result = db.session.query(
                ScheduleORM,
                ScriptORM.name.label('script_name'),
                AWSProfileORM.name.label('profile_name'),
                UserORM.username
            ).join(
                ScriptORM, ScheduleORM.script_id == ScriptORM.id
            ).join(
                AWSProfileORM, ScheduleORM.profile_id == AWSProfileORM.id
            ).join(
                UserORM, ScheduleORM.user_id == UserORM.id
            ).filter(
                ScheduleORM.id == schedule_id
            ).first()
            
            if not result:
                return None
            
            # Process result
            schedule = result[0].to_dict()  # Get Schedule object and convert to dict
            schedule['script_name'] = result.script_name
            schedule['profile_name'] = result.profile_name
            schedule['username'] = result.username
            
            # Format parameters
            if schedule['parameters']:
                try:
                    schedule['parameters'] = json.loads(schedule['parameters'])
                except:
                    schedule['parameters'] = {}
            
            return schedule
    
    def create_schedule(self, script_id, profile_id, user_id, schedule_type, schedule_value, parameters=None):
        """Create a new schedule with validation"""
        try:
            with self.app.app_context():
                # Import the model here to avoid circular imports
                from app.models.scheduler_orm import ScheduleORM
                
                # Validate script exists
                script = ScriptORM.query.get(script_id)
                if not script:
                    return {
                        'success': False,
                        'message': 'Script not found'
                    }
                
                # Validate profile exists
                profile = AWSProfileORM.query.get(profile_id)
                if not profile:
                    return {
                        'success': False,
                        'message': 'AWS profile not found'
                    }
                
                # Validate schedule type
                if schedule_type not in ['daily', 'interval']:
                    return {
                        'success': False,
                        'message': 'Invalid schedule type'
                    }
                
                # Validate schedule value based on type
                if schedule_type == 'daily':
                    if schedule_value not in self.ALLOWED_TIME_SLOTS:
                        return {
                            'success': False,
                            'message': 'Invalid schedule time. Please select from available options.'
                        }
                elif schedule_type == 'interval':
                    if schedule_value not in self.ALLOWED_INTERVALS:
                        return {
                            'success': False,
                            'message': 'Invalid interval. Please select from available options.'
                        }
                
                # Calculate next run time
                next_run = self._calculate_next_run(schedule_type, schedule_value)
                
                # Store parameters as JSON
                parameters_json = json.dumps(parameters) if parameters else None
                
                # Create the schedule
                schedule = ScheduleORM(
                    script_id=script_id,
                    profile_id=profile_id,
                    user_id=user_id,
                    schedule_type=schedule_type,
                    schedule_value=schedule_value,
                    enabled=1,
                    parameters=parameters_json,
                    next_run=next_run,
                    created_at=datetime.now().isoformat()
                )
                
                # Save to database
                db.session.add(schedule)
                db.session.commit()
                
                # Add job to scheduler
                job = self._add_job(
                    schedule.id,
                    script_id,
                    profile_id,
                    user_id,
                    schedule_type,
                    schedule_value,
                    parameters or {}
                )
                
                return {
                    'success': True,
                    'id': schedule.id,
                    'job_id': job.id if job else None,
                    'next_run': job.next_run_time.isoformat() if job and job.next_run_time else None
                }
        
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            return {
                'success': False,
                'message': f'Server error: {str(e)}'
            }
    
    def update_schedule(self, schedule_id, enabled=None, schedule_type=None, schedule_value=None, profile_id=None, parameters=None):
        """Update an existing schedule with validation"""
        try:
            with self.app.app_context():
                # Import the model here to avoid circular imports
                from app.models.scheduler_orm import ScheduleORM
                import time
                
                # Get current schedule
                schedule = ScheduleORM.query.get(schedule_id)
                
                if not schedule:
                    return {
                        'success': False,
                        'message': 'Schedule not found'
                    }
                
                # Prepare to track changes
                changes_made = False
                interval_changed = False
                old_schedule_type = schedule.schedule_type
                old_schedule_value = schedule.schedule_value
                
                # Update schedule type if provided
                if schedule_type is not None:
                    # Validate schedule type
                    if schedule_type not in ['daily', 'interval']:
                        return {
                            'success': False,
                            'message': 'Invalid schedule type'
                        }
                    
                    # Check if schedule type is changing
                    if schedule_type != schedule.schedule_type:
                        interval_changed = True
                        
                    schedule.schedule_type = schedule_type
                    changes_made = True
                
                # Update schedule value if provided
                if schedule_value is not None:
                    # Validate schedule value based on type
                    current_type = schedule_type if schedule_type is not None else schedule.schedule_type
                    
                    if current_type == 'daily':
                        if schedule_value not in self.ALLOWED_TIME_SLOTS:
                            return {
                                'success': False,
                                'message': 'Invalid schedule time. Please select from available options.'
                            }
                    
                    elif current_type == 'interval':
                        if schedule_value not in self.ALLOWED_INTERVALS:
                            return {
                                'success': False,
                                'message': 'Invalid interval. Please select from available options.'
                            }
                    
                    # Check if interval value is changing
                    if schedule_value != schedule.schedule_value:
                        interval_changed = True
                        
                    schedule.schedule_value = schedule_value
                    changes_made = True
                
                # Update enabled status if provided
                if enabled is not None:
                    schedule.enabled = 1 if enabled else 0
                    changes_made = True
                
                # Update profile if provided
                if profile_id is not None:
                    # Check if profile exists
                    profile = AWSProfileORM.query.get(profile_id)
                    if not profile:
                        return {
                            'success': False,
                            'message': 'AWS profile not found'
                        }
                    
                    schedule.profile_id = profile_id
                    changes_made = True
                
                # Update parameters if provided
                if parameters is not None:
                    schedule.parameters = json.dumps(parameters)
                    changes_made = True
                
                if not changes_made:
                    return {
                        'success': False,
                        'message': 'No fields to update'
                    }
                
                # Reset the timestamp if the interval or schedule type changed
                if interval_changed:
                    logger.info(f"Schedule interval changed from {old_schedule_type}/{old_schedule_value} to {schedule.schedule_type}/{schedule.schedule_value}")
                    logger.info(f"Resetting start_timestamp for schedule {schedule_id}")
                    
                    # Reset the start timestamp to now since interval changed
                    schedule.start_timestamp = time.time()
                
                # Calculate new next_run if schedule type or value changed
                if schedule_type is not None or schedule_value is not None:
                    next_run = self._calculate_next_run(
                        schedule.schedule_type,
                        schedule.schedule_value
                    )
                    schedule.next_run = next_run
                
                # Save changes to database
                db.session.commit()
                
                # Handle job updates
                if schedule.enabled == 0:
                    # Remove job if disabled
                    self._remove_job(schedule.job_id)
                    return {
                        'success': True,
                        'message': 'Schedule disabled'
                    }
                else:
                    # Update or add job
                    job = self._add_job(
                        schedule.id,
                        schedule.script_id,
                        schedule.profile_id,
                        schedule.user_id,
                        schedule.schedule_type,
                        schedule.schedule_value,
                        json.loads(schedule.parameters) if schedule.parameters else {}
                    )
                    
                    return {
                        'success': True, 
                        'next_run': job.next_run_time.isoformat() if job and job.next_run_time else None
                    }
        
        except Exception as e:
            logger.error(f"Error updating schedule: {str(e)}")
            return {
                'success': False,
                'message': f'Server error: {str(e)}'
            }
    
    def delete_schedule(self, schedule_id):
        """Delete a schedule"""
        try:
            with self.app.app_context():
                # Import the model here to avoid circular imports
                from app.models.scheduler_orm import ScheduleORM
                
                # Get schedule
                schedule = ScheduleORM.query.get(schedule_id)
                
                if not schedule:
                    return {'success': False, 'message': 'Schedule not found'}
                
                # Get job_id before deleting
                job_id = schedule.job_id
                
                # Delete from database
                db.session.delete(schedule)
                db.session.commit()
                
                # Remove from scheduler
                self._remove_job(job_id)
                
                return {'success': True}
        
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}
    
    def manual_run(self, schedule_id):
        """Manually run a scheduled script"""
        try:
            with self.app.app_context():
                # Import the model here to avoid circular imports
                from app.models.scheduler_orm import ScheduleORM
                
                # Get schedule
                schedule = ScheduleORM.query.get(schedule_id)
                
                if not schedule:
                    return {'success': False, 'message': 'Schedule not found'}
                
                parameters = json.loads(schedule.parameters) if schedule.parameters else {}
                
                if not self.run_script_func:
                    return {'success': False, 'message': 'Run script function not set'}
                
                # Run the script
                execution_id = self.run_script_func(
                    schedule.script_id,
                    schedule.profile_id,
                    schedule.user_id,
                    parameters
                )
                
                if execution_id:
                    return {'success': True, 'execution_id': execution_id}
                else:
                    return {'success': False, 'message': 'Failed to start script execution'}
        
        except Exception as e:
            logger.error(f"Error running scheduled script: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if hasattr(self, 'scheduler') and self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
    
    def _add_job(self, schedule_id, script_id, profile_id, user_id, schedule_type, schedule_value, parameters):
        """Add a job to the scheduler"""
        if not self.run_script_func:
            logger.error("Cannot add job: run_script_func not set")
            return None
            
        with self.app.app_context():
            # Import here to avoid circular imports
            from app.models.scheduler_orm import ScheduleORM
            schedule = ScheduleORM.query.get(schedule_id)
            
            # Handle different schedule types
            if schedule_type == 'daily':
                # Parse time (format: "HH:MM")
                hour, minute = schedule_value.split(':')
                trigger = CronTrigger(hour=hour, minute=minute)
                job_id = f"daily_{script_id}_{schedule_id}"
            elif schedule_type == 'interval':
                # Create job ID first so we can use it in logging
                job_id = f"interval_{script_id}_{schedule_id}"
                
                # Special handling for debug interval
                if schedule_value == "debug-3min":
                    # 3-minute debug interval
                    logger.info(f"Setting up special debug interval: 3 minutes for job {job_id}")
                    interval_minutes = 3
                else:
                    # Regular hour-based intervals
                    hours_interval = int(schedule_value)
                    interval_minutes = hours_interval * 60
                    logger.info(f"Setting up interval schedule: {hours_interval} hours ({interval_minutes} minutes) for job {job_id}")
                
                # Get current time and prepare for timestamp calculations
                import time
                now = datetime.now()
                current_timestamp = time.time()
                logger.info(f"Current timestamp: {current_timestamp}")
                
                # Check if we have a start timestamp (for persistent timing across restarts)
                if schedule and schedule.start_timestamp:
                    try:
                        # Calculate time since the initial start using the persisted timestamp
                        elapsed_since_start = current_timestamp - schedule.start_timestamp
                        interval_seconds = interval_minutes * 60
                        
                        # Calculate how much of the current interval has elapsed
                        elapsed_in_current = elapsed_since_start % interval_seconds
                        
                        # Calculate remaining time in the current interval
                        remaining_seconds = interval_seconds - elapsed_in_current
                        
                        # If very little time remains (<10 seconds), move to the next interval to avoid immediate triggers
                        if remaining_seconds < 10:
                            remaining_seconds += interval_seconds
                        
                        # Next run is now plus the remaining time
                        adjusted_next_run = now + timedelta(seconds=remaining_seconds)
                        
                        logger.info(f"Using stored start timestamp: {schedule.start_timestamp}")
                        logger.info(f"Time elapsed since start: {elapsed_since_start:.2f}s")
                        logger.info(f"Elapsed in current interval: {elapsed_in_current:.2f}s, remaining: {remaining_seconds:.2f}s")
                        logger.info(f"Calculated next_run after restart: {adjusted_next_run.isoformat()}")
                        logger.info(f"Time remaining until next run: {remaining_seconds/60:.2f} minutes")
                        
                        trigger = IntervalTrigger(minutes=interval_minutes, start_date=adjusted_next_run)
                        
                    except (ValueError, TypeError) as e:
                        # If there's any issue with timestamp calculations, fall back to next_run if available
                        logger.warning(f"Error using start_timestamp for job {job_id}: {e}, falling back to next_run")
                        
                        # Try to use next_run as a fallback
                        if schedule.next_run:
                            try:
                                next_run_time = datetime.fromisoformat(schedule.next_run)
                                
                                if next_run_time > now:
                                    # Next run is in the future, use it directly
                                    logger.info(f"Using fallback next_run time: {schedule.next_run}")
                                    trigger = IntervalTrigger(minutes=interval_minutes, start_date=next_run_time)
                                else:
                                    # Next run is in the past, use default interval
                                    logger.info(f"Next run is in the past, using default interval")
                                    trigger = IntervalTrigger(minutes=interval_minutes)
                            except Exception as e2:
                                logger.warning(f"Error parsing next_run fallback: {e2}, using default interval")
                                trigger = IntervalTrigger(minutes=interval_minutes)
                        else:
                            # No valid next_run, use default interval
                            logger.warning("No valid next_run time available, using default interval")
                            trigger = IntervalTrigger(minutes=interval_minutes)
                        
                # If no start timestamp, try to use next_run time
                elif schedule and schedule.next_run:
                    try:
                        next_run_time = datetime.fromisoformat(schedule.next_run)
                        
                        if next_run_time > now:
                            # Next run is in the future, use the stored next_run directly
                            logger.info(f"Using stored next_run time for job {job_id}: {schedule.next_run}")
                            trigger = IntervalTrigger(minutes=interval_minutes, start_date=next_run_time)
                            
                            # Also set the start timestamp for future restarts
                            schedule.start_timestamp = current_timestamp - ((next_run_time - now).total_seconds() % (interval_minutes * 60))
                            logger.info(f"Setting derived start_timestamp: {schedule.start_timestamp}")
                            db.session.commit()
                        else:
                            # Next run is in the past, use a new interval and set start timestamp
                            logger.info(f"Next run {schedule.next_run} is in the past, using new interval")
                            trigger = IntervalTrigger(minutes=interval_minutes)
                            
                            # Set start timestamp for future restarts
                            schedule.start_timestamp = current_timestamp
                            logger.info(f"Setting new start_timestamp: {schedule.start_timestamp}")
                            db.session.commit()
                    except (ValueError, TypeError) as e:
                        # If there's any issue parsing the stored time, fall back to default
                        logger.warning(f"Error parsing stored next_run for job {job_id}: {e}, using default interval")
                        trigger = IntervalTrigger(minutes=interval_minutes)
                        
                        # Set start timestamp for future restarts
                        schedule.start_timestamp = current_timestamp
                        logger.info(f"Setting fallback start_timestamp: {schedule.start_timestamp}")
                        db.session.commit()
                else:
                    # No existing next_run or start_timestamp, use standard interval
                    logger.info(f"No existing timing info for job {job_id}, using standard interval")
                    trigger = IntervalTrigger(minutes=interval_minutes)
                    
                    # If we have a schedule object, set start timestamp for future restarts
                    if schedule:
                        schedule.start_timestamp = current_timestamp
                        logger.info(f"Setting initial start_timestamp: {schedule.start_timestamp}")
                        db.session.commit()
                
            else:
                logger.error(f"Unknown schedule type: {schedule_type}")
                return None
            
            try:
                # Add the job to the scheduler
                job = self.scheduler.add_job(
                    self.run_script_func,
                    trigger=trigger,
                    args=[script_id, profile_id, user_id, parameters, job_id],  # Pass job_id to run_script_func
                    id=job_id,
                    replace_existing=True
                )
                
                # Update job_id and next_run in database
                self._update_job_info(schedule_id, job)
                
                logger.info(f"Added job {job_id} to scheduler")
                return job
            except Exception as e:
                logger.error(f"Error adding job: {str(e)}")
                return None
    
    def _update_job_info(self, schedule_id, job):
        """Update job information in the database"""
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        with self.app.app_context():
            # Import the model here to avoid circular imports
            from app.models.scheduler_orm import ScheduleORM
            import time
            
            # Get schedule
            schedule = ScheduleORM.query.get(schedule_id)
            
            if not schedule:
                logger.error(f"Schedule not found for ID {schedule_id}")
                return
            
            # Update fields
            schedule.job_id = job.id
            schedule.next_run = next_run
            
            # Set/update timestamp info for interval schedules
            if schedule.schedule_type == 'interval' and job.next_run_time:
                # If no start timestamp exists, initialize it
                if not schedule.start_timestamp:
                    # Record the current timestamp as reference point
                    schedule.start_timestamp = time.time()
                    logger.info(f"Setting initial start_timestamp for job {job.id}: {schedule.start_timestamp}")
            
            # Save changes
            db.session.commit()
    
    def _remove_job(self, job_id):
        """Remove a job from the scheduler"""
        if not job_id:
            return
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id} from scheduler")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
    
    def _calculate_next_run(self, schedule_type, schedule_value):
        """Calculate the next run time for a schedule"""
        now = datetime.now()
        
        if schedule_type == 'daily':
            # Parse time (format: "HH:MM")
            hour, minute = map(int, schedule_value.split(':'))
            
            # Create next run date
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has already passed today, move to tomorrow
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule_type == 'interval':
            # Handle special debug interval
            if schedule_value == "debug-3min":
                minutes_interval = 3
            else:
                # Regular hour-based intervals
                hours_interval = int(schedule_value)
                minutes_interval = hours_interval * 60
            
            # Next run is 'minutes_interval' from now
            next_run = now + timedelta(minutes=minutes_interval)
        
        else:
            # Default if schedule type is unknown
            next_run = now + timedelta(hours=1)
        
        return next_run.isoformat()
        
    def update_next_run_after_execution(self, job_id):
        """Update the next_run time in the database after a successful execution"""
        if not job_id:
            logger.warning("Cannot update next_run: no job_id provided")
            return False
            
        try:
            # Get the job from APScheduler
            job = self.scheduler.get_job(job_id)
            if not job or not job.next_run_time:
                logger.warning(f"Cannot update next_run: job {job_id} not found or has no next_run_time")
                return False
                
            # Extract schedule_id from job_id (format is 'interval_script_id_schedule_id' or 'daily_script_id_schedule_id')
            parts = job_id.split('_')
            if len(parts) < 3:
                logger.warning(f"Cannot update next_run: invalid job_id format: {job_id}")
                return False
                
            # The last part is the schedule_id
            schedule_id = parts[-1]
            
            # Update the database
            with self.app.app_context():
                from app.models.scheduler_orm import ScheduleORM
                import time
                
                schedule = ScheduleORM.query.get(schedule_id)
                if not schedule:
                    logger.warning(f"Cannot update next_run: schedule {schedule_id} not found")
                    return False
                
                # Update the next_run time
                schedule.next_run = job.next_run_time.isoformat()
                
                # Update last_run time to now
                schedule.last_run = datetime.now().isoformat()
                
                # If this is an interval schedule, we don't update the start_timestamp
                # That's our reference point for calculating intervals after restart
                
                logger.info(f"Updated next_run for schedule {schedule_id} to {schedule.next_run}")
                logger.info(f"Updated last_run for schedule {schedule_id} to {schedule.last_run}")
                
                # Commit to database
                from app.utils.db import db
                db.session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating next_run after execution: {str(e)}", exc_info=True)
            return False

# Create an instance using ORM mode
scheduler_service = SchedulerService()