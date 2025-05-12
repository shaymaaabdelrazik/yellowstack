from flask import Blueprint, request, jsonify
from app.services import setting_service
import logging

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
setting_api = Blueprint('setting_api', __name__, url_prefix='/api/settings')

# Get all settings
@setting_api.route('', methods=['GET'])
def get_settings():
    """Get all settings"""
    settings = setting_service.get_all_settings()
    
    return jsonify({
        'success': True,
        'settings': settings
    })

# Update settings
@setting_api.route('', methods=['POST'])
def update_settings():
    """Update settings"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No settings provided'
        }), 400
    
    # Update settings
    setting_service.update_multiple_settings(data) if hasattr(setting_service, 'update_multiple_settings') else setting_service.setting_adapter.update_multiple(data)
    
    return jsonify({
        'success': True
    })

# Get a specific setting
@setting_api.route('/<key>', methods=['GET'])
def get_setting(key):
    """Get a setting by key"""
    value = setting_service.get_setting(key) if hasattr(setting_service, 'get_setting') else setting_service.setting_adapter.get(key)
    
    if value is None:
        return jsonify({
            'success': False,
            'message': 'Setting not found'
        }), 404
    
    return jsonify({
        'success': True,
        'key': key,
        'value': value
    })

# Update a specific setting
@setting_api.route('/<key>', methods=['PUT'])
def update_setting(key):
    """Update a setting"""
    data = request.json
    
    if not data or 'value' not in data:
        return jsonify({
            'success': False,
            'message': 'Setting value is required'
        }), 400
    
    # Update setting
    setting_service.set_setting(key, data['value']) if hasattr(setting_service, 'set_setting') else setting_service.setting_adapter.set(key, data['value'])
    
    return jsonify({
        'success': True
    })

# Delete a setting
@setting_api.route('/<key>', methods=['DELETE'])
def delete_setting(key):
    """Delete a setting"""
    success = setting_service.delete_setting(key) if hasattr(setting_service, 'delete_setting') else setting_service.setting_adapter.delete(key)
    
    if not success:
        return jsonify({
            'success': False,
            'message': 'Setting not found'
        }), 404
    
    return jsonify({
        'success': True
    })