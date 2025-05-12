from flask import Blueprint, request, jsonify
from app.services import aws_service
import logging

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
aws_profile_api = Blueprint('aws_profile_api', __name__, url_prefix='/api/aws_profiles')

# Get all AWS profiles
@aws_profile_api.route('', methods=['GET'])
def get_aws_profiles():
    """Get all AWS profiles"""
    profiles = aws_service.get_all_profiles()
    
    return jsonify({
        'success': True,
        'profiles': profiles
    })

# Add a new AWS profile
@aws_profile_api.route('', methods=['POST'])
def add_aws_profile():
    """Add a new AWS profile"""
    data = request.json
    
    if not data or not data.get('name') or not data.get('aws_access_key') or not data.get('aws_secret_key') or not data.get('aws_region'):
        return jsonify({
            'success': False,
            'message': 'All fields are required'
        }), 400
    
    try:
        # Create a new AWS profile
        profile_id = aws_service.create_profile(
            name=data.get('name'),
            aws_access_key=data.get('aws_access_key'),
            aws_secret_key=data.get('aws_secret_key'),
            aws_region=data.get('aws_region'),
            is_default=data.get('is_default', False)
        )
        
        return jsonify({
            'success': True,
            'profile_id': profile_id
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

# Get an AWS profile by ID
@aws_profile_api.route('/<int:profile_id>', methods=['GET'])
def get_aws_profile(profile_id):
    """Get an AWS profile"""
    profile = aws_service.get_profile_by_id(profile_id)
    
    if not profile:
        return jsonify({
            'success': False,
            'message': 'Profile not found'
        }), 404
    
    return jsonify({
        'success': True,
        'profile': profile.to_dict()
    })

# Update an AWS profile
@aws_profile_api.route('/<int:profile_id>', methods=['PUT'])
def update_aws_profile(profile_id):
    """Update an AWS profile"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    try:
        # Update the profile
        success = aws_service.update_profile(
            profile_id=profile_id,
            name=data.get('name'),
            aws_access_key=data.get('aws_access_key'),
            aws_secret_key=data.get('aws_secret_key'),
            aws_region=data.get('aws_region'),
            is_default=data.get('is_default')
        )
        
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

# Delete an AWS profile
@aws_profile_api.route('/<int:profile_id>', methods=['DELETE'])
def delete_aws_profile(profile_id):
    """Delete an AWS profile"""
    try:
        # Delete the profile
        aws_service.delete_profile(profile_id)

        # Always return a valid JSON response
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error deleting profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Internal server error"
        }), 500

# Set an AWS profile as default
@aws_profile_api.route('/<int:profile_id>/set_default', methods=['POST'])
def set_default_aws_profile(profile_id):
    """Set an AWS profile as default"""
    try:
        # Set as default
        aws_service.set_default_profile(profile_id)
        
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400