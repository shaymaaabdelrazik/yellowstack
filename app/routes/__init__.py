# Import all routes to make them available when importing from routes package
from app.routes.script_api import script_api
from app.routes.aws_profile_api import aws_profile_api
from app.routes.user_api import user_api
from app.routes.execution_api import execution_api
from app.routes.setting_api import setting_api
from app.routes.views import views
from app.routes.scheduler_api import scheduler_api

# List of all blueprints for easy access
all_blueprints = [
    script_api,
    aws_profile_api,
    user_api,
    execution_api,
    setting_api,
    views,
    scheduler_api
]

__all__ = [
    'script_api', 
    'aws_profile_api', 
    'user_api', 
    'execution_api', 
    'setting_api', 
    'views',
    'scheduler_api',
    # Blueprint collection
    'all_blueprints'
]