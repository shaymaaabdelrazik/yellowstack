import os
import secrets

class Config:
    """Base configuration class for the application"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(24))
    
    # Database settings
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'yellowstack.db'))
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF settings
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour in seconds
    # Uncomment the line below if you need to disable Referer check
    # WTF_CSRF_CHECK_REFERER = False
    
    # Logging settings
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/yellowstack/app.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Default settings
    HISTORY_LIMIT = 10  # Default number of execution history entries to show
    
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    ENABLE_AI_HELP = os.environ.get('ENABLE_AI_HELP', 'true')
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Override session cookie settings for development
    SESSION_COOKIE_SECURE = False
    
    # Enable more verbose logging
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    
    # Use in-memory database for testing
    DATABASE = os.environ.get('TEST_DATABASE_PATH', ':memory:')
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Ensure secure cookies in production
    SESSION_COOKIE_SECURE = True
    
    # Stricter same-site cookie policy
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Configure for production performance
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    def __init__(self):
        # This should always be set in production through environment variable
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("No SECRET_KEY set for production configuration!")

# Dictionary of available configurations
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Function to get config by name
def get_config(config_name='default'):
    """
    Get application configuration by name
    
    Args:
        config_name (str): Name of the configuration to use
                           (development, testing, production, or default)
    
    Returns:
        Config object for the specified environment
    """
    return config_by_name.get(config_name, config_by_name['default'])