from flask import Blueprint, request, jsonify, session
from app.services.scheduler_service import scheduler_service
import logging

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
scheduler_api = Blueprint('scheduler_api', __name__, url_prefix='/api')

# Main API endpoint for scheduler
@scheduler_api.route('/scheduler', methods=['GET'])
def get_scheduler_base():
    """Base endpoint for scheduler API"""
    return jsonify({
        'success': True,
        'message': 'Scheduler API is available',
        'endpoints': {
            'schedules': 'Get all schedules',
            'schedules/{id}': 'Get, update, or delete a specific schedule',
            'schedules/{id}/run': 'Run a scheduled script immediately'
        }
    })

@scheduler_api.route('/schedules', methods=['GET'])
def get_schedules():
    """Get all schedules with option to include disabled ones"""
    try:
        include_disabled = request.args.get('include_disabled', 'false').lower() == 'true'
        schedules = scheduler_service.get_schedules(include_disabled)
        
        return jsonify({
            'success': True,
            'schedules': schedules
        })
    except Exception as e:
        logger.error(f"Error getting schedules: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Error retrieving schedules"
        }), 500

@scheduler_api.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Get a specific schedule"""
    try:
        schedule = scheduler_service.get_schedule(schedule_id)
        
        if not schedule:
            return jsonify({
                'success': False,
                'message': 'Schedule not found'
            }), 404
            
        return jsonify({
            'success': True,
            'schedule': schedule
        })
    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Internal server error"
        }), 500

@scheduler_api.route('/schedules', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    try:
        data = request.json
        
        if not data or not data.get('script_id') or not data.get('profile_id') or \
           not data.get('schedule_type') or not data.get('schedule_value'):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
            
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User not authenticated'
            }), 401
        
        result = scheduler_service.create_schedule(
            script_id=data.get('script_id'),
            profile_id=data.get('profile_id'),
            user_id=user_id,
            schedule_type=data.get('schedule_type'),
            schedule_value=data.get('schedule_value'),
            parameters=data.get('parameters')
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Error creating schedule"
        }), 500

@scheduler_api.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing schedule"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
            
        result = scheduler_service.update_schedule(
            schedule_id=schedule_id,
            enabled=data.get('enabled'),
            schedule_type=data.get('schedule_type'),
            schedule_value=data.get('schedule_value'),
            profile_id=data.get('profile_id'),
            parameters=data.get('parameters')
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Internal server error"
        }), 500

@scheduler_api.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        result = scheduler_service.delete_schedule(schedule_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Internal server error"
        }), 500

@scheduler_api.route('/schedules/<int:schedule_id>/run', methods=['POST'])
def run_schedule_now(schedule_id):
    """Run a scheduled script immediately"""
    try:
        result = scheduler_service.manual_run(schedule_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error running schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': "Internal server error"
        }), 500