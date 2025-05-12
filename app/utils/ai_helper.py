import logging
import openai
from app.models import SettingORM

# Get the existing logger from the application
logger = logging.getLogger('yellowstack')

def get_ai_help(error_output):
    """
    Get AI analysis of script execution error.
    Uses OpenAI GPT-4 to analyze AWS script errors and provide solutions.
    
    Args:
        error_output (str): The error output from the script execution
        
    Returns:
        tuple: (analysis, solution) where analysis is the error analysis and 
               solution is the proposed fix
    """
    # Check if AI help is enabled in settings
    enable_ai_help = SettingORM.get('enable_ai_help', 'true')
    if enable_ai_help.lower() == 'false':
        return "AI assistance is disabled in settings. Enable it to get error analysis.", None
    
    # Check for API key
    api_key = SettingORM.get('openai_api_key')
    if not api_key:
        return "OpenAI API key not configured. Please set it in the settings.", None

    # Create OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Set up the system prompt for consistent response format
        system_prompt = (
            "You are an AWS error‐analysis assistant. "
            "Always respond in exactly two clearly labeled sections:\n\n"
            "Analysis:\n<your analysis text here>\n\n"
            "Solution:\n<your proposed fix here>"
        )
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"Error output:\n\n{error_output}"}
            ]
        )
        
        # Extract the response content
        ai_response = response.choices[0].message.content.strip()

        # Parse the response into analysis and solution sections
        parts = ai_response.split("Solution:", 1)
        analysis = parts[0].replace("Analysis:", "").strip()

        solution = None
        if len(parts) > 1:
            solution = parts[1].strip()
        else:
            # Fallback: use second sentence of full response as solution
            sentences = ai_response.split('.')
            solution = sentences[1].strip() if len(sentences) > 1 else "No solution provided."

        return analysis, solution

    except Exception as e:
        logger.error(f"Error getting AI help: {str(e)}")
        return f"Error getting AI help: {e}", None