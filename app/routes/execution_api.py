from flask import Blueprint, request, jsonify, session
from app.services import execution_service
import logging
import json

# Create logger
logger = logging.getLogger('yellowstack')

# Create blueprint
execution_api = Blueprint('execution_api', __name__, url_prefix='/api')

# Main API endpoint for executions
@execution_api.route('/executions', methods=['GET'])
def get_executions_base():
    """Base endpoint for executions API"""
    return jsonify({
        'success': True,
        'message': 'Executions API is available',
        'endpoints': {
            'recent_executions': 'Get recent executions',
            'execution_details': 'Get execution details by ID',
            'run_script': 'Run a script',
            'execution_history': 'Get execution history',
            'execution_stats': 'Get execution statistics',
            'ai_help': 'Get AI help for failed executions',
            'cancel_execution': 'Cancel a running execution',
            'provide_input': 'Provide input to an interactive script'
        }
    })

# Get recent executions for the dashboard
@execution_api.route('/recent_executions', methods=['GET'])
def get_recent_executions():
    """Get recent executions for the dashboard"""
    # Get recent executions
    executions = execution_service.get_recent_executions()
    
    return jsonify({
        'success': True,
        'executions': executions
    })

# Get execution details
@execution_api.route('/execution_details/<int:execution_id>', methods=['GET'])
def get_execution_details(execution_id):
    """Get execution details"""
    try:
        # Get execution
        execution = execution_service.get_execution_by_id(execution_id)
        
        if not execution:
            return jsonify({
                'success': False,
                'message': 'Execution record not found'
            }), 404
        
        return jsonify({
            'success': True,
            'execution': execution
        })
    
    except Exception as e:
        logger.error(f"Error getting execution details for ID {execution_id}: {str(e)}")

        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Run a script
@execution_api.route('/run_script', methods=['POST'])
def run_script_api():
    """Run a script with optional region override"""
    data = request.json
    
    if not data or not data.get('script_id') or not data.get('profile_id'):
        return jsonify({
            'success': False,
            'message': 'Script ID and profile ID are required'
        }), 400
    
    try:
        # Get current user ID from session
        user_id = session.get('user_id')
        
        # Extract parameters if provided
        parameters_json = data.get('parameters')
        parameters = json.loads(parameters_json) if parameters_json else None
        
        # Run the script
        execution_id = execution_service.run_script(
            script_id=data.get('script_id'),
            profile_id=data.get('profile_id'),
            user_id=user_id,
            parameters=parameters,
            region_override=data.get('region_override')
        )
        
        return jsonify({
            'success': True,
            'execution_id': execution_id
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error running script: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Get execution history with pagination and filters
@execution_api.route('/execution_history', methods=['GET'])
def get_execution_history():
    """Get execution history with pagination and filters"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        
        # Get filter parameters
        script_id = request.args.get('script_id', type=int)
        status = request.args.get('status')
        date = request.args.get('date')
        user_id = request.args.get('user_id', type=int)
        
        # Build filters
        filters = {}
        if script_id:
            filters['script_id'] = script_id
        if status:
            filters['status'] = status
        if date:
            filters['date'] = date
        if user_id:
            filters['user_id'] = user_id
        
        # Get execution history
        result = execution_service.get_execution_history(page, filters=filters)
        
        return jsonify({
            'success': True,
            'executions': result['executions'],
            'current_page': result['current_page'],
            'total_pages': result['total_pages'],
            'total_count': result['total_count']
        })
    except Exception as e:
        logger.error(f"Error getting execution history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Get execution statistics for dashboard chart
@execution_api.route('/execution_stats', methods=['GET'])
def get_execution_stats():
    """Get statistics about script executions for the dashboard chart"""
    try:
        # Get the number of days (default: 7)
        days = request.args.get('days', 7, type=int)
        
        # Get statistics
        chart_data = execution_service.get_execution_stats(days)
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        logger.error(f"Error in execution_stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading chart data'
        }), 500

# Get AI help for a failed execution
@execution_api.route('/ai_help/<int:execution_id>', methods=['GET'])
def get_ai_help_route(execution_id):
    """Get AI help for a failed execution"""
    try:
        # Get AI help
        result = execution_service.get_ai_help(execution_id)
        
        return jsonify({
            'success': True,
            'error': result.get('error', ''),
            'ai_help': result.get('ai_help', ''),
            'solution': result.get('solution', '')
        })
    except ValueError as e:
        error_message = str(e)
        if "OpenAI API key not configured" in error_message:
            return jsonify({
                'success': True,
                'ai_help': "AI assistance is disabled. Please configure an OpenAI API key in Settings.",
                'solution': "Go to Settings and enter a valid OpenAI API key to enable AI assistance."
            })
        elif "AI help is disabled" in error_message:
            return jsonify({
                'success': True, 
                'ai_help': "AI assistance is disabled in Settings.",
                'solution': "Go to Settings and enable AI assistance to use this feature."
            })
        else:
            return jsonify({
                'success': False,
                'message': error_message
            }), 404
    except Exception as e:
        logger.error(f"Error getting AI help: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Cancel a running execution
@execution_api.route('/cancel_execution/<int:execution_id>', methods=['POST'])
def cancel_execution(execution_id):
    """Cancel a running script execution"""
    try:
        # Cancel the execution
        execution_service.cancel_execution(execution_id)
        
        return jsonify({
            'success': True,
            'message': 'Execution cancelled successfully'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error canceling execution: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Provide input to an interactive script
@execution_api.route('/provide_input/<int:execution_id>', methods=['POST'])
def provide_input(execution_id):
    """Provide input to an interactive script"""
    data = request.json
    
    if not data or 'input' not in data:
        return jsonify({
            'success': False,
            'message': 'Input is required'
        }), 400
    
    try:
        # Provide input
        execution_service.provide_input(execution_id, data['input'])
        
        return jsonify({
            'success': True
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error providing input: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500