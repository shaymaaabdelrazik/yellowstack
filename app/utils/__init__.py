# Import utility functions to make them available at the module level
from app.utils.ai_helper import get_ai_help
from app.utils.db import db

# Export the utility functions
__all__ = ['db', 'get_ai_help']