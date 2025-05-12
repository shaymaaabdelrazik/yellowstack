# Import all services to make them available when importing from services package
from app.services.script_service import ScriptService, script_service
from app.services.aws_service import AWSService, aws_service
from app.services.execution_service import ExecutionService, execution_service
from app.services.auth_service import AuthService, auth_service
from app.services.setting_service import SettingService, setting_service

# Import scheduler service directly from its module
from app.services.scheduler_service import scheduler_service

# Import adapter classes
from app.services.user_adapter import UserAdapter
from app.services.script_adapter import ScriptAdapter
from app.services.aws_profile_adapter import AWSProfileAdapter
from app.services.execution_adapter import ExecutionAdapter
from app.services.setting_adapter import SettingAdapter

# Import adapters as singleton instances
from app.services.user_adapter import user_adapter
from app.services.script_adapter import script_adapter
from app.services.aws_profile_adapter import aws_profile_adapter
from app.services.execution_adapter import execution_adapter
from app.services.setting_adapter import setting_adapter

__all__ = [
    # Services
    'ScriptService', 'script_service',
    'AWSService', 'aws_service',
    'ExecutionService', 'execution_service',
    'AuthService', 'auth_service',
    'SettingService', 'setting_service',
    'scheduler_service',
    
    # Adapters
    'UserAdapter', 'user_adapter',
    'ScriptAdapter', 'script_adapter',
    'AWSProfileAdapter', 'aws_profile_adapter',
    'ExecutionAdapter', 'execution_adapter',
    'SettingAdapter', 'setting_adapter'
]