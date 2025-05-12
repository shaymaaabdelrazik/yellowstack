"""
Tests for application initialization in app/__init__.py
"""
import os
import pytest
from unittest.mock import patch, MagicMock, call

from app import (
    create_app, 
    register_blueprints,
    init_services,
    init_extensions,
    socketio,
    csrf
)

class TestAppInit:
    """
    Test cases for application initialization functions
    """
    
    def test_create_app_loads_configs(self):
        """Test app creation loads appropriate configs"""
        # We can't patch Flask constructor directly, so instead we'll patch the config methods
        with patch('app.register_blueprints') as mock_register_blueprints, \
             patch('app.init_services') as mock_init_services, \
             patch('app.init_extensions') as mock_init_extensions, \
             patch('app.setup_logging') as mock_setup_logging, \
             patch('app.utils.db.init_db_sqlalchemy') as mock_init_db, \
             patch('os.makedirs') as mock_makedirs, \
             patch('flask.Config.from_object') as mock_from_object, \
             patch('flask.Config.from_pyfile') as mock_from_pyfile:
            
            # Call create_app
            app = create_app()
            
            # Verify the right config methods were called
            mock_from_object.assert_called_once_with('app.config.DevelopmentConfig')
            mock_from_pyfile.assert_called_once_with('config.py', silent=True)
            
            # Verify other setup calls were made
            mock_setup_logging.assert_called_once()
            mock_init_db.assert_called_once()
            mock_init_services.assert_called_once()
            mock_register_blueprints.assert_called_once()
            mock_init_extensions.assert_called_once()
            
            # Basic verification that app is initialized
            assert app.config is not None
    
    def test_create_app_with_test_config(self):
        """Test app creation with test configuration"""
        test_config = {
            'TESTING': True,
            'SECRET_KEY': 'test_key',
            'DATABASE': ':memory:',
            'CUSTOM_SETTING': 'custom_value'
        }
        
        with patch('app.register_blueprints') as mock_register_blueprints, \
             patch('app.init_services') as mock_init_services, \
             patch('app.init_extensions') as mock_init_extensions, \
             patch('app.setup_logging') as mock_setup_logging, \
             patch('app.utils.db.init_db_sqlalchemy') as mock_init_db, \
             patch('os.makedirs') as mock_makedirs, \
             patch('flask.Config.from_object') as mock_from_object, \
             patch('flask.Config.from_mapping') as mock_from_mapping, \
             patch('flask.Config.from_pyfile') as mock_from_pyfile:
            
            # Call create_app with test_config
            app = create_app(test_config)
            
            # Verify test config was applied
            mock_from_mapping.assert_called_once()
            mock_from_object.assert_called_once()  # Will still be called before from_mapping
            mock_from_pyfile.assert_not_called()   # Shouldn't be called when test_config provided
    
    @patch('app.routes.views')
    @patch('app.routes.user_api.user_api')
    @patch('app.routes.script_api.script_api')
    @patch('app.routes.aws_profile_api.aws_profile_api')
    @patch('app.routes.execution_api.execution_api')
    @patch('app.routes.setting_api.setting_api')
    @patch('app.routes.scheduler_api.scheduler_api')
    def test_register_blueprints(self, mock_scheduler_api, mock_setting_api, 
                               mock_execution_api, mock_aws_profile_api, 
                               mock_script_api, mock_user_api, mock_views):
        """Test blueprint registration"""
        # Create a mock Flask app
        mock_app = MagicMock()
        
        # Call register_blueprints
        result = register_blueprints(mock_app)
        
        # Verify all blueprints were registered
        assert mock_app.register_blueprint.call_count == 7
        
        # Verify specific blueprints were registered
        mock_app.register_blueprint.assert_any_call(mock_views)
        mock_app.register_blueprint.assert_any_call(mock_user_api)
        mock_app.register_blueprint.assert_any_call(mock_script_api)
        mock_app.register_blueprint.assert_any_call(mock_aws_profile_api)
        mock_app.register_blueprint.assert_any_call(mock_execution_api)
        mock_app.register_blueprint.assert_any_call(mock_setting_api)
        mock_app.register_blueprint.assert_any_call(mock_scheduler_api)
        
        # Verify function returns the app
        assert result == mock_app
    
    @patch('app.services.script_service')
    @patch('app.services.aws_service')
    @patch('app.services.execution_service')
    @patch('app.services.scheduler_service.scheduler_service')
    def test_init_services(self, mock_scheduler_service, mock_execution_service, 
                          mock_aws_service, mock_script_service):
        """Test service initialization"""
        # Create a mock Flask app
        mock_app = MagicMock()
        
        # Call init_services
        result = init_services(mock_app)
        
        # Verify execution service was initialized with socketio and app
        mock_execution_service.set_socketio.assert_called_once_with(socketio)
        mock_execution_service.set_flask_app.assert_called_once_with(mock_app)
        
        # Verify scheduler service was initialized
        mock_scheduler_service.init_app.assert_called_once()
        
        # Verify first arg is app
        assert mock_scheduler_service.init_app.call_args[0][0] == mock_app
        
        # Verify function returns the app
        assert result == mock_app
    
    def test_init_extensions(self):
        """Test extension initialization"""
        # Create a mock Flask app
        mock_app = MagicMock()
        
        # Mock socketio and csrf objects
        mock_socketio = MagicMock()
        mock_csrf_protect = MagicMock()
        
        # Patch atexit and extensions
        with patch('app.socketio', mock_socketio), \
             patch('app.csrf', mock_csrf_protect), \
             patch('atexit.register') as mock_atexit_register:
            
            # Call init_extensions
            result = init_extensions(mock_app)
            
            # Verify socketio was initialized
            mock_socketio.init_app.assert_called_once_with(
                mock_app, 
                cors_allowed_origins="*", 
                async_mode="eventlet", 
                manage_session=False
            )
            
            # Verify CSRF protection was initialized
            mock_csrf_protect.init_app.assert_called_once_with(mock_app)
            
            # Verify atexit handler was registered
            assert mock_atexit_register.call_count == 1
            
            # Verify function returns the app
            assert result == mock_app

def test_flask_extensions():
    """Test that key flask extensions are properly initialized"""
    # Verify that flask extensions are present
    from app import socketio, csrf
    
    # Verify they are of the expected types
    from flask_socketio import SocketIO
    from flask_wtf.csrf import CSRFProtect
    
    assert isinstance(socketio, SocketIO)
    assert isinstance(csrf, CSRFProtect)