import json
from datetime import datetime
from app.utils.db import db

class ExecutionORM(db.Model):
    """SQLAlchemy ORM model for execution_history table"""
    
    __tablename__ = 'execution_history'
    
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id', ondelete='SET NULL'), nullable=True)
    aws_profile_id = db.Column(db.Integer, db.ForeignKey('aws_profiles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default="Pending")
    start_time = db.Column(db.String(40), nullable=True)
    end_time = db.Column(db.String(40), nullable=True)
    output = db.Column(db.Text, nullable=True)
    ai_analysis = db.Column(db.Text, nullable=True)
    ai_solution = db.Column(db.Text, nullable=True)
    parameters = db.Column(db.Text, nullable=True)
    is_scheduled = db.Column(db.Integer, default=0)
    
    # Define relationships
    script = db.relationship('ScriptORM', backref=db.backref('executions', passive_deletes=True))
    user = db.relationship('UserORM', backref='executions')
    
    def __init__(self, script_id=None, aws_profile_id=None, user_id=None,
                 status="Pending", start_time=None, end_time=None, output=None,
                 ai_analysis=None, ai_solution=None, parameters=None, is_scheduled=0):
        """Initialize a new execution"""
        self.script_id = script_id
        self.aws_profile_id = aws_profile_id
        self.user_id = user_id
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.output = output
        self.ai_analysis = ai_analysis
        self.ai_solution = ai_solution
        self.parameters = parameters
        self.is_scheduled = is_scheduled
    
    @classmethod
    def get_by_id(cls, execution_id):
        """Get an execution by ID"""
        return db.session.get(cls, execution_id)
    
    @classmethod
    def get_by_id_with_details(cls, execution_id):
        """Get an execution by ID with related data as dictionary"""
        execution = db.session.get(cls, execution_id)
        
        if not execution:
            return None
            
        result = execution.to_dict()
        
        # Add related data
        if execution.script:
            result['script_name'] = execution.script.name
            result['script_path'] = execution.script.path
        
        if execution.aws_profile:
            result['aws_profile_name'] = execution.aws_profile.name
        
        if execution.user:
            result['username'] = execution.user.username
            
        return result
    
    @classmethod
    def get_recent(cls, limit=10):
        """Get recent executions"""
        executions = cls.query.order_by(cls.id.desc()).limit(limit).all()
        
        result = []
        for execution in executions:
            execution_dict = execution.to_dict()
            
            # Add related data
            if execution.script:
                execution_dict['script_name'] = execution.script.name
            
            if execution.aws_profile:
                execution_dict['aws_profile_name'] = execution.aws_profile.name
            
            if execution.user:
                execution_dict['username'] = execution.user.username
                
            result.append(execution_dict)
            
        return result
    
    @classmethod
    def get_history(cls, page=1, per_page=10, filters=None):
        """Get execution history with pagination and filters"""
        # Start with base query
        query = cls.query
        
        # Apply filters
        if filters:
            if 'script_id' in filters and filters['script_id']:
                query = query.filter(cls.script_id == filters['script_id'])
            
            if 'status' in filters and filters['status']:
                query = query.filter(cls.status == filters['status'])
            
            if 'date' in filters and filters['date']:
                query = query.filter(db.func.date(cls.start_time) == filters['date'])
            
            if 'user_id' in filters and filters['user_id']:
                query = query.filter(cls.user_id == filters['user_id'])
        
        # Get total count for pagination
        total_count = query.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get paginated results
        executions = query.order_by(cls.id.desc()).paginate(page=page, per_page=per_page)
        
        # Prepare result
        result = []
        for execution in executions.items:
            execution_dict = execution.to_dict()
            
            # Add related data
            if execution.script:
                execution_dict['script_name'] = execution.script.name
            
            if execution.aws_profile:
                execution_dict['aws_profile_name'] = execution.aws_profile.name
            
            if execution.user:
                execution_dict['username'] = execution.user.username
                
            result.append(execution_dict)
        
        return {
            'executions': result,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count
        }
    
    @classmethod
    def get_stats(cls, days=7):
        """Get execution statistics for the dashboard chart"""
        # Calculate stats by date and status
        stats = db.session.query(
            db.func.date(cls.start_time).label('execution_date'),
            cls.status,
            db.func.count().label('count')
        ).filter(
            cls.start_time.isnot(None),
            cls.start_time >= db.func.datetime('now', f'-{days} days')
        ).group_by(
            db.func.date(cls.start_time),
            cls.status
        ).order_by(
            db.func.date(cls.start_time)
        ).all()
        
        # Get unique dates
        dates = db.session.query(
            db.func.date(cls.start_time).label('execution_date')
        ).filter(
            cls.start_time.isnot(None),
            cls.start_time >= db.func.datetime('now', f'-{days} days')
        ).group_by(
            db.func.date(cls.start_time)
        ).order_by(
            db.func.date(cls.start_time)
        ).all()
        
        # Prepare data for chart
        chart_data = []
        for date_row in dates:
            date_str = date_row.execution_date
            
            # Create entry for this date
            date_entry = {
                'date': date_str,
                'Success': 0,
                'Failed': 0,
                'Running': 0,
                'Cancelled': 0
            }
            
            # Fill counts for each status
            for stat in stats:
                if stat.execution_date == date_str:
                    date_entry[stat.status] = stat.count
            
            chart_data.append(date_entry)
        
        return chart_data
    
    def save(self):
        """Save the execution to the database"""
        db.session.add(self)
        db.session.commit()
        return self.id
    
    def update_status(self, status, output=None):
        """Update the status of the execution"""
        self.status = status
        
        # Set end time if completed
        if status in ['Success', 'Failed', 'Cancelled']:
            self.end_time = datetime.now().isoformat()
        
        # Update output if provided
        if output is not None:
            self.output = output if self.output is None else self.output + output
        
        db.session.commit()
    
    def append_output(self, output):
        """Append output to the execution"""
        self.output = output if self.output is None else self.output + output
        db.session.commit()
    
    def update_ai_analysis(self, analysis, solution):
        """Update AI analysis for the execution"""
        self.ai_analysis = analysis
        self.ai_solution = solution
        db.session.commit()
    
    def cancel(self):
        """Cancel the execution"""
        if self.status != 'Running':
            return False
        
        self.status = 'Cancelled'
        self.end_time = datetime.now().isoformat()
        
        # Append message to output
        self.output = (self.output or '') + '\n[SYSTEM] Script execution was cancelled by user.'
        
        db.session.commit()
        return True
    
    def to_dict(self):
        """Convert Execution object to dictionary"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'aws_profile_id': self.aws_profile_id,
            'user_id': self.user_id,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'output': self.output,
            'ai_analysis': self.ai_analysis,
            'ai_solution': self.ai_solution,
            'parameters': self.parameters,
            'is_scheduled': self.is_scheduled
        }
    
    def parse_parameters(self):
        """Parse the parameters JSON string to a Python object"""
        if not self.parameters:
            return {}
            
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}