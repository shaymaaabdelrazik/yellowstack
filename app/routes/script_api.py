from flask import Blueprint, request, jsonify, session
from app.services import script_service
import os
import json
import logging

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
script_api = Blueprint('script_api', __name__, url_prefix='/api/scripts')

# Get all scripts
@script_api.route('', methods=['GET'])
def get_scripts():
    """Get all scripts"""
    scripts = script_service.get_all_scripts()
    
    return jsonify({
        'success': True,
        'scripts': scripts
    })

# Add a new script
@script_api.route('', methods=['POST'])
def add_script():
    """Add a new script"""
    data = request.json
    
    if not data or not data.get('name') or not data.get('path'):
        return jsonify({
            'success': False,
            'message': 'Name and path are required'
        }), 400
    
    # Get user ID from session
    user_id = session.get('user_id')
    
    try:
        # Create a new script
        script_id = script_service.create_script(
            name=data.get('name'),
            description=data.get('description', ''),
            path=data.get('path'),
            parameters=data.get('parameters'),
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'script_id': script_id
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

# Get a script by ID
@script_api.route('/<int:script_id>', methods=['GET'])
def get_script(script_id):
    """Get a script by ID"""
    script = script_service.get_script_by_id(script_id)
    
    if not script:
        return jsonify({
            'success': False,
            'message': 'Script not found'
        }), 404
    
    return jsonify({
        'success': True,
        'script': script.to_dict()
    })

# Update a script
@script_api.route('/<int:script_id>', methods=['PUT'])
def update_script(script_id):
    """Update script details"""
    data = request.json
    
    try:
        # Update the script
        success = script_service.update_script(
            script_id=script_id,
            name=data.get('name'),
            description=data.get('description'),
            path=data.get('path') if 'path' in data else None,
            parameters=data.get('parameters') if 'parameters' in data else None
        )
        
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

# Delete a script
@script_api.route('/<int:script_id>', methods=['DELETE'])
def delete_script(script_id):
    """Delete a script"""
    try:
        # Delete the script
        success = script_service.delete_script(script_id)
        
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400