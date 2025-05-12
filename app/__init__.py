import os

# Import timezone configuration
try:
    from app.utils.timezone_config import *  # pragma: no cover
except ImportError:  # pragma: no cover
    pass
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

# Initialize SocketIO for real-time communication
socketio = SocketIO()

# Initialize CSRF protection
csrf = CSRFProtect()

# Import SQLAlchemy instance
from app.utils.db import db

def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config: Configuration to use for testing (optional)
        
    Returns:
        Flask: The configured Flask application
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True, 
                static_folder='../static', template_folder='../templates')
    
    # Load default configuration
    app.config.from_object('app.config.DevelopmentConfig')
    
    # Override with instance config if it exists
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:  # pragma: no cover
        pass
    
    # Configure logging
    setup_logging(app)
    
    # Initialize database
    from app.utils.db import init_db_sqlalchemy, db
    
    # SQLAlchemy ORM connection
    init_db_sqlalchemy(app)
    
    # Initialize services
    init_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize extensions
    init_extensions(app)
    
    return app

def setup_logging(app):  # pragma: no cover
    """Configure application logging"""
    log_dir = '/var/log/yellowstack'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10485760,  # 10 MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Set up logger
    logger = logging.getLogger('yellowstack')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Log application startup
    logger.info('Application starting')
    
    return logger

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints
    from app.routes import views
    
    # Import API blueprints
    from app.routes.user_api import user_api
    from app.routes.script_api import script_api
    from app.routes.aws_profile_api import aws_profile_api
    from app.routes.execution_api import execution_api
    from app.routes.setting_api import setting_api
    from app.routes.scheduler_api import scheduler_api
    
    # Register each blueprint
    app.register_blueprint(views)
    
    # Register API blueprints
    app.register_blueprint(user_api)
    app.register_blueprint(script_api)
    app.register_blueprint(aws_profile_api)
    app.register_blueprint(execution_api)
    app.register_blueprint(setting_api)
    app.register_blueprint(scheduler_api)
    
    return app

def init_services(app):
    """Initialize application services"""
    # Import service instances
    from app.services import (
        script_service, aws_service, execution_service
    )
    
    # Import and initialize scheduler service
    from app.services.scheduler_service import scheduler_service
    
    # Initialize the execution service with SocketIO and Flask app
    execution_service.set_socketio(socketio)
    execution_service.set_flask_app(app)
    
    # Initialize the scheduler
    def run_script_wrapper(script_id, profile_id, user_id, parameters=None, job_id=None):  # pragma: no cover
        """Wrapper for scheduler to run scripts"""
        # The scheduler context needs the app context
        # Store app reference for later use in thread
        from app.services.execution_service import ExecutionService
        
        with app.app_context():
            # Pass the app context explicitly when running from scheduler
            return execution_service.run_script(
                script_id, profile_id, user_id, 
                parameters, is_scheduled=1, 
                job_id=job_id  # Pass job_id to execution service
            )
    
    scheduler_service.init_app(app, run_script_wrapper)
    
    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    # Initialize SocketIO with the app
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet", manage_session=False)
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Register cleanup function that only runs on actual app shutdown, not request teardown
    import atexit
    
    def cleanup_processes():  # pragma: no cover
        """Terminate any running processes when the application completely shuts down"""
        from app.services.execution_service import running_processes
        import psutil
        import logging
        
        logger = logging.getLogger('yellowstack')
        
        if running_processes:
            logger.info(f"Application shutdown: Cleaning up {len(running_processes)} running processes")
            for execution_id, process in list(running_processes.items()):
                try:
                    if process and process.poll() is None:  # Process is still running
                        try:
                            # Terminate the process and all its children
                            parent = psutil.Process(process.pid)
                            for child in parent.children(recursive=True):
                                try:
                                    child.terminate()
                                except (psutil.NoSuchProcess, ProcessLookupError):
                                    pass
                            
                            # Terminate parent process
                            parent.terminate()
                            logger.info(f"Terminated process for execution {execution_id} during shutdown")
                        except (psutil.NoSuchProcess, ProcessLookupError, Exception) as e:
                            logger.warning(f"Error terminating process {execution_id} during shutdown: {str(e)}")
                except Exception as e:
                    logger.error(f"Error during process cleanup for execution {execution_id}: {str(e)}")
                    
    # Register the cleanup function to run on application exit, not per-request
    atexit.register(cleanup_processes)
    
    return app

# Schedule timeout checker for executions
def schedule_execution_timeout_check():  # pragma: no cover
    """Schedule a task to check for hung executions"""
    from app.services import execution_service
    import threading
    
    # Run the check every 5 minutes
    threading.Timer(300, schedule_execution_timeout_check).start()
    execution_service.check_hung_executions()