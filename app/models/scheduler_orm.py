from app.utils.db import db
from datetime import datetime

class ScheduleORM(db.Model):
    """SQLAlchemy ORM model for schedules table"""
    
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id', ondelete='CASCADE'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('aws_profiles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_type = db.Column(db.String(32), nullable=False)
    schedule_value = db.Column(db.String(32), nullable=False)
    enabled = db.Column(db.Integer, nullable=False, default=1)
    parameters = db.Column(db.Text, nullable=True)
    job_id = db.Column(db.String(64), nullable=True)
    next_run = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.String(32), default=lambda: datetime.now().isoformat())
    last_run = db.Column(db.String(32), nullable=True)
    start_timestamp = db.Column(db.Float, nullable=True)
    
    # Define relationships
    script = db.relationship('ScriptORM', backref=db.backref('schedules', lazy=True, cascade='all, delete-orphan'))
    profile = db.relationship('AWSProfileORM', backref=db.backref('schedules', lazy=True))
    user = db.relationship('UserORM', backref=db.backref('schedules', lazy=True))
    
    def __init__(self, script_id=None, profile_id=None, user_id=None, schedule_type=None, 
                 schedule_value=None, enabled=1, parameters=None, job_id=None, next_run=None, created_at=None,
                 last_run=None, start_timestamp=None):
        """Initialize a new schedule"""
        self.script_id = script_id
        self.profile_id = profile_id
        self.user_id = user_id
        self.schedule_type = schedule_type
        self.schedule_value = schedule_value
        self.enabled = enabled
        self.parameters = parameters
        self.job_id = job_id
        self.next_run = next_run
        self.created_at = created_at or datetime.now().isoformat()
        self.last_run = last_run
        self.start_timestamp = start_timestamp
    
    def to_dict(self):
        """Convert Schedule object to dictionary"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'schedule_type': self.schedule_type,
            'schedule_value': self.schedule_value,
            'enabled': self.enabled,
            'parameters': self.parameters,
            'job_id': self.job_id,
            'next_run': self.next_run,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'start_timestamp': self.start_timestamp
        }