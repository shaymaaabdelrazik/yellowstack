import os
import json
import logging
import subprocess
import threading
import signal
import psutil
from datetime import datetime, timedelta
import openai
from flask_socketio import emit
from app.models import ExecutionORM
from app.services.execution_adapter import execution_adapter
from app.services.script_adapter import script_adapter
from app.services.aws_profile_adapter import aws_profile_adapter
from app.services.setting_adapter import setting_adapter

logger = logging.getLogger('yellowstack')

# Store reference to SocketIO instance
socketio = None

# Queue for each execution to handle interactive input
input_queues = {}

# Dictionary to track running processes
running_processes = {}

class ExecutionService:
    """Service for managing script executions using the ORM adapters"""
    
    def __init__(self, use_orm=True):
        """
        Initialize the execution service
        """
        self.socketio_instance = None
        self.execution_adapter = execution_adapter
        self.script_adapter = script_adapter
        self.aws_profile_adapter = aws_profile_adapter
        self.setting_adapter = setting_adapter
        
        # Set use_orm for all adapters
        self.execution_adapter.use_orm = True
        self.script_adapter.use_orm = True
        self.aws_profile_adapter.use_orm = True
        self.setting_adapter.use_orm = True
    
    def set_socketio(self, socket_instance):
        """Set the SocketIO instance for emitting events"""
        global socketio
        socketio = socket_instance
        self.socketio_instance = socket_instance
        
    def set_flask_app(self, app):
        """Set the Flask app for use in threads"""
        # Store the app for use in threads
        self.app = app
    
    def get_recent_executions(self, limit=10):
        """Get recent executions for the dashboard"""
        return self.execution_adapter.get_recent(limit)
    
    def get_execution_by_id(self, execution_id):
        """Get an execution by ID with details (as dictionary)"""
        return self.execution_adapter.get_by_id_with_details(execution_id)
    
    def get_execution_history(self, page=1, per_page=None, filters=None):
        """Get execution history with pagination and filters"""
        if per_page is None:
            # Get the value from settings
            per_page = self.setting_adapter.get('history_limit', 10)
            # Convert to integer, as the value from DB comes as string
            try:
                per_page = int(per_page)
            except (ValueError, TypeError):
                per_page = 10

        return self.execution_adapter.get_history(page, per_page, filters)
    
    def get_execution_stats(self, days=7):
        """Get statistics about script executions for the dashboard chart"""
        return self.execution_adapter.get_stats(days)
    
    def run_script(self, script_id, profile_id, user_id, parameters=None, region_override=None, is_scheduled=0, job_id=None):
        """Run a script with the given parameters"""
        # Get script and profile
        script = self.script_adapter.get_by_id(script_id)
        profile = self.aws_profile_adapter.get_by_id(profile_id)
        
        if not script:
            raise ValueError("Script not found")
        
        if not profile:
            raise ValueError("AWS profile not found")
        
        # Create execution record
        execution_id = self.execution_adapter.create(
            script_id=script.id,
            aws_profile_id=profile.id,
            user_id=user_id,
            status="Pending",
            parameters=json.dumps(parameters) if parameters else None,
            is_scheduled=is_scheduled
        )
        
        # Prepare AWS environment variables
        aws_env = os.environ.copy()
        aws_env['AWS_ACCESS_KEY_ID'] = profile.aws_access_key
        aws_env['AWS_SECRET_ACCESS_KEY'] = profile.aws_secret_key
        
        # Use region override if provided, otherwise use profile's region
        region = region_override if region_override else profile.aws_region
        aws_env['AWS_DEFAULT_REGION'] = region
        
        # Parse parameters for script execution
        script_params = []
        if parameters:
            for key, value in parameters.items():
                if key == 'verbose' and value:  # For flags without values
                    script_params.append(f'--{key}')
                elif value:  # For parameters with values
                    script_params.extend([f'--{key}', str(value)])
        
        # Get the current Flask app for the thread
        try:
            from flask import current_app
            flask_app = current_app._get_current_object()
        except RuntimeError:
            flask_app = None

        # Start script in a thread
        thread = threading.Thread(
            target=self._run_script_thread, 
            args=(execution_id, script.path, aws_env, script_params, flask_app, is_scheduled, job_id)
        )
        thread.daemon = True
        thread.start()
        
        return execution_id
    
    def cancel_execution(self, execution_id):
        """Cancel a running script execution"""
        from flask import current_app
        flask_app = current_app._get_current_object()
        
        with flask_app.app_context():
            # Get the execution
            execution_dict = self.execution_adapter.get_by_id_with_details(execution_id)
            
            if not execution_dict:
                raise ValueError("Execution not found")
            
            if execution_dict['status'] != 'Running':
                raise ValueError("Cannot cancel execution that is not running")
            
            # Flag this execution as explicitly cancelled in the database first
            self.execution_adapter.update_status(
                execution_id=execution_id,
                status="Cancelled",
                output="\n[SYSTEM] Cancellation requested by user - terminating process..."
            )
            
            # Check if we have a reference to the running process
            process = running_processes.get(execution_id)
            if process and process.poll() is None:  # Process exists and is still running
                try:
                    # Log that we're about to terminate the process
                    logger.info(f"Terminating process for execution {execution_id} with PID {process.pid}")
                    
                    # Terminate the process and all its children
                    parent = psutil.Process(process.pid)
                    children = []
                    try:
                        children = parent.children(recursive=True)
                        for child in children:
                            try:
                                logger.info(f"Terminating child process with PID {child.pid}")
                                child.terminate()  # Try to terminate gracefully
                            except psutil.NoSuchProcess:
                                pass  # Process already terminated
                    except Exception as e:
                        logger.error(f"Error getting child processes: {str(e)}")
                    
                    # Terminate parent process
                    parent.terminate()
                    
                    # Wait for process to terminate (with timeout)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if not terminated gracefully
                        logger.warning(f"Process {process.pid} did not terminate gracefully, force killing")
                        try:
                            for child in children:
                                try:
                                    child.kill()  # Force kill
                                except psutil.NoSuchProcess:
                                    pass  # Process already terminated
                        except Exception as e:
                            logger.error(f"Error killing child processes: {str(e)}")
                            
                        try:
                            parent.kill()  # Force kill parent
                        except Exception as e:
                            logger.error(f"Error killing parent process: {str(e)}")
                    
                    logger.info(f"Process for execution {execution_id} terminated successfully")
                    
                    # Remove from tracking dictionary
                    del running_processes[execution_id]
                except (psutil.NoSuchProcess, ProcessLookupError) as e:
                    logger.warning(f"Process for execution {execution_id} no longer exists: {str(e)}")
                except Exception as e:
                    logger.error(f"Error terminating process for execution {execution_id}: {str(e)}", exc_info=True)
            else:
                logger.warning(f"No running process found for execution {execution_id}")
            
            # We've already set the status to Cancelled, so we just need to capture success
            success = True
            
            # Update completion message
            self.execution_adapter.append_output(
                execution_id, 
                "\n[SYSTEM] Process terminated successfully."
            )
        
        # Emit status update
        if success and socketio:
            socketio.emit('script_status_update', {
                'execution_id': execution_id,
                'script_id': execution_dict['script_id'],
                'status': 'Cancelled'
            })
        
        return success
    
    def get_ai_help(self, execution_id):
        """Get AI help for a failed execution"""
        from flask import current_app
        flask_app = current_app._get_current_object()
        
        with flask_app.app_context():
            # Get the execution
            execution_dict = self.execution_adapter.get_by_id_with_details(execution_id)
            
            if not execution_dict or execution_dict['status'] != 'Failed':
                raise ValueError("Failed execution not found")
            
            # If there's already saved analysis, return it
            if execution_dict.get('ai_analysis') and execution_dict.get('ai_solution'):
                return {
                    'error': execution_dict['output'],
                    'ai_help': execution_dict['ai_analysis'],
                    'solution': execution_dict['ai_solution']
                }
            
            # Check if AI help is enabled (using the lowercase version first, which is set in the UI)
            ai_help_enabled = self.setting_adapter.get('enable_ai_help')
            if ai_help_enabled is None:
                # If not found, try the uppercase version as fallback
                ai_help_enabled = self.setting_adapter.get('ENABLE_AI_HELP', 'true')

            # Convert to lowercase and check if it's 'true'
            if ai_help_enabled.lower() != 'true':
                raise ValueError("AI help is disabled in settings")
            
            # Try to get API key from settings (check both keys)
            api_key = self.setting_adapter.get('OPENAI_API_KEY', None)
            if not api_key or api_key == "sk-dummy-key-for-testing":
                # Try the lowercase version used in the UI
                api_key = self.setting_adapter.get('openai_api_key', None)
            
            if not api_key or api_key == "sk-dummy-key-for-testing":
                raise ValueError("OpenAI API key not configured")
            
            # Get script information
            script = self.script_adapter.get_by_id(execution_dict['script_id'])
            if not script:
                raise ValueError("Script not found")
            
            # Analyze the error with OpenAI
            analysis, solution = self._analyze_error_with_openai(
                script.name, 
                script.path, 
                execution_dict['output'],
                api_key
            )
            
            # Save the analysis
            self.execution_adapter.update_ai_analysis(execution_id, analysis, solution)
            
            return {
                'error': execution_dict['output'],
                'ai_help': analysis,
                'solution': solution
            }
    
    def provide_input(self, execution_id, input_text):
        """Provide input to an interactive script"""
        global input_queues
        
        if execution_id not in input_queues:
            raise ValueError("No interactive execution found")
        
        # Add newline to input
        input_text += '\n'
        
        # Add input to the queue
        input_queues[execution_id].put(input_text)
        
        return True
    
    def check_hung_executions(self):
        """Check for executions that have been running for too long"""
        from flask import current_app
        from sqlalchemy import text
        from app.utils.db import db
        
        flask_app = current_app._get_current_object()
        
        with flask_app.app_context():
            # Check the EXECUTION_TIMEOUT setting
            timeout_setting = self.setting_adapter.get('EXECUTION_TIMEOUT', '30')
            try:
                timeout_minutes = int(timeout_setting)
            except ValueError:
                timeout_minutes = 30
            
            # Calculate the cutoff time
            cutoff_time = (datetime.now() - timedelta(minutes=timeout_minutes)).isoformat()
            
            # Using SQLAlchemy to query for hung executions
            hung_executions = ExecutionORM.query.filter(
                ExecutionORM.status == 'Running',
                ExecutionORM.start_time < cutoff_time
            ).all()
            
            # Mark each hung execution as failed
            for execution in hung_executions:
                execution_id = execution.id
                script_id = execution.script_id
                
                # Update the execution status
                self.execution_adapter.update_status(
                    execution_id=execution_id,
                    status="Failed",
                    output="\n[SYSTEM] Script execution timed out and was automatically terminated."
                )
                
                # Emit status update
                if socketio:
                    socketio.emit('script_status_update', {
                        'execution_id': execution_id,
                        'script_id': script_id,
                        'status': 'Failed'
                    })
                
                logger.warning(f"Execution {execution_id} (script: {script_id}) marked as failed due to timeout")
    
    def _run_script_thread(self, execution_id, script_path, env_vars, script_params, flask_app, is_scheduled=0, job_id=None):
        """Run a script in a thread and capture output"""
        global input_queues, running_processes
        from queue import Queue
        
        # Create input queue for this execution
        input_queues[execution_id] = Queue()
        
        # Use Flask app context
        if flask_app:
            app_context = flask_app.app_context()
            app_context.push()
        
        try:
            # Update status to Running
            self.execution_adapter.update_status(
                execution_id=execution_id,
                status="Running",
                output="[SYSTEM] Starting script execution...\n"
            )
            
            # Emit status update
            if socketio:
                socketio.emit('script_status_update', {
                    'execution_id': execution_id,
                    'status': 'Running'
                })
            
            # Assemble command
            command = ['python', script_path] + script_params
            
            # Start the process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env=env_vars,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            # Store the process in the global dictionary
            running_processes[execution_id] = process
            
            # Read output and update execution
            output_buffer = ""
            last_update_time = datetime.now()
            
            while True:
                # Check if there's input in the queue
                if not input_queues[execution_id].empty():
                    input_text = input_queues[execution_id].get()
                    process.stdin.write(input_text)
                    process.stdin.flush()
                    
                    # Echo input to output
                    output_buffer += f"[INPUT]: {input_text}"
                    
                    # Update execution more frequently when there's interaction
                    self.execution_adapter.append_output(execution_id, output_buffer)
                    output_buffer = ""
                    last_update_time = datetime.now()
                
                # Read output
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                
                if output_line:
                    # Add line to buffer
                    output_buffer += output_line
                    
                    # Emit output to socket
                    if socketio:
                        socketio.emit('script_output', {
                            'execution_id': execution_id,
                            'output': output_line
                        })
                    
                    # Update execution in database periodically
                    time_since_update = (datetime.now() - last_update_time).total_seconds()
                    if time_since_update > 1.0 or len(output_buffer) > 1000:
                        self.execution_adapter.append_output(execution_id, output_buffer)
                        output_buffer = ""
                        last_update_time = datetime.now()
            
            # Get return code
            return_code = process.poll()
            
            # Write any remaining output
            if output_buffer:
                self.execution_adapter.append_output(execution_id, output_buffer)
            
            # Update status based on return code
            # Only mark as cancelled if it was explicitly cancelled by the user
            # Checking if we previously marked this execution for cancellation
            execution = self.execution_adapter.get_by_id(execution_id)
            if execution and execution.status == "Cancelled":
                final_status = "Cancelled"
                output_message = "\n[SYSTEM] Script execution was terminated by user"
            elif return_code == -15:
                # If we got SIGTERM but didn't explicitly cancel, treat as a failure
                logger.warning(f"Execution {execution_id} received SIGTERM but wasn't explicitly cancelled")
                final_status = "Failed"
                output_message = "\n[SYSTEM] Script execution was terminated unexpectedly (signal 15)"
            # Normal exit
            elif return_code == 0:
                final_status = "Success"
                output_message = "\n[SYSTEM] Script execution completed successfully"
            # Any other non-zero exit code
            else:
                final_status = "Failed"
                output_message = f"\n[SYSTEM] Script execution failed with return code {return_code}"
                
            self.execution_adapter.update_status(
                execution_id=execution_id,
                status=final_status,
                output=output_message
            )
            
            # Emit status update
            if socketio:
                socketio.emit('script_status_update', {
                    'execution_id': execution_id,
                    'status': final_status
                })
                
            logger.info(f"Script execution {execution_id} completed with status: {final_status}")
            
            # Update next_run time in scheduler if this was a scheduled execution and was successful
            if is_scheduled == 1 and final_status == "Success" and job_id:
                try:
                    # Import here to avoid circular imports
                    from app.services.scheduler_service import scheduler_service
                    # Update the next run time in the database
                    scheduler_service.update_next_run_after_execution(job_id)
                    logger.info(f"Updated next_run time for job {job_id} after successful execution")
                except Exception as e:
                    logger.error(f"Error updating next_run time for job {job_id}: {str(e)}", exc_info=True)
            
        except Exception as e:
            # Handle any exceptions in the thread
            error_message = f"\n[SYSTEM] Error running script: {str(e)}"
            self.execution_adapter.update_status(
                execution_id=execution_id,
                status="Failed",
                output=error_message
            )
            
            # Emit status update
            if socketio:
                socketio.emit('script_status_update', {
                    'execution_id': execution_id,
                    'status': 'Failed'
                })
                
            logger.error(f"Error in script execution {execution_id}: {str(e)}", exc_info=True)
            
        finally:
            # Clean up
            if flask_app:
                app_context.pop()
            
            # Remove input queue
            if execution_id in input_queues:
                del input_queues[execution_id]
                
            # Remove process from tracking dictionary
            if execution_id in running_processes:
                del running_processes[execution_id]
    
    def _analyze_error_with_openai(self, script_name, script_path, error_output, api_key):
        """Analyze a script error using OpenAI API"""
        try:
            # Read script content
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Limit script content size
            if len(script_content) > 2000:
                script_content = script_content[:2000] + "\n...(truncated)..."
            
            # Limit error output size
            if len(error_output) > 2000:
                error_output = error_output[-2000:] + "\n...(truncated)..."
            
            # Setup OpenAI API client (new API style)
            client = openai.OpenAI(api_key=api_key)
            
            # Create message for analysis
            analysis_prompt = f"""
            Analyze this script error and identify the likely cause:
            
            Script Name: {script_name}
            
            Script Content:
            ```python
            {script_content}
            ```
            
            Error Output:
            ```
            {error_output}
            ```
            
            Provide a concise analysis of what went wrong.
            """
            
            # Get analysis (new API style)
            analysis_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Python and AWS expert helping to debug script errors."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis = analysis_response.choices[0].message.content.strip()
            
            # Create message for solution
            solution_prompt = f"""
            Based on this error in a Python AWS script, suggest a solution:
            
            Script Name: {script_name}
            
            Error Output:
            ```
            {error_output}
            ```
            
            Your Analysis:
            {analysis}
            
            Provide a concise, practical solution to fix this error. Include code examples if helpful.
            """
            
            # Get solution (new API style)
            solution_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Python and AWS expert helping to debug script errors."},
                    {"role": "user", "content": solution_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # New API response structure
            solution = solution_response.choices[0].message.content.strip()
            
            return analysis, solution
            
        except Exception as e:
            logger.error(f"Error analyzing script error with OpenAI: {str(e)}", exc_info=True)
            return (
                "Error analysis could not be performed.",
                f"AI analysis failed: {str(e)}"
            )

# Create an instance using ORM mode
execution_service = ExecutionService()