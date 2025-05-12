import pytest
from unittest.mock import patch, MagicMock
from app.utils.ai_helper import get_ai_help

class MockOpenAIResponse:
    """Mock OpenAI API response"""
    def __init__(self, content):
        self.choices = [
            MagicMock(
                message=MagicMock(
                    content=content
                )
            )
        ]

def test_ai_help_disabled(app):
    """Test get_ai_help when AI assistance is disabled in settings"""
    with app.app_context():
        # Mock SettingORM.get to return 'false' for 'enable_ai_help'
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            mock_get.return_value = 'false'
            
            # Call get_ai_help
            analysis, solution = get_ai_help("Some error output")
            
            # Verify the correct message is returned
            assert "AI assistance is disabled" in analysis
            assert solution is None
            
            # Verify SettingORM.get was called with correct parameter
            mock_get.assert_called_once_with('enable_ai_help', 'true')

def test_ai_help_no_api_key(app):
    """Test get_ai_help when the OpenAI API key is not configured"""
    with app.app_context():
        # Mock SettingORM.get to return appropriate values
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            def mock_get_side_effect(key, default=None):
                if key == 'enable_ai_help':
                    return 'true'
                if key == 'openai_api_key':
                    return None
                return default
            
            mock_get.side_effect = mock_get_side_effect
            
            # Call get_ai_help
            analysis, solution = get_ai_help("Some error output")
            
            # Verify the correct message is returned
            assert "OpenAI API key not configured" in analysis
            assert solution is None

def test_ai_help_successful_response(app):
    """Test get_ai_help with a successful OpenAI API response"""
    with app.app_context():
        # Mock SettingORM.get to return appropriate values
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            def mock_get_side_effect(key, default=None):
                if key == 'enable_ai_help':
                    return 'true'
                if key == 'openai_api_key':
                    return 'fake-api-key'
                return default
            
            mock_get.side_effect = mock_get_side_effect
            
            # Mock OpenAI client and response
            mock_client = MagicMock()
            mock_response = MockOpenAIResponse("Analysis: This is an analysis of the error.\n\nSolution: This is a proposed solution.")
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock OpenAI.OpenAI to return mock_client
            with patch('app.utils.ai_helper.openai.OpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                # Call get_ai_help
                analysis, solution = get_ai_help("Some AWS S3 permission error")
                
                # Verify analysis and solution are extracted correctly
                assert analysis == "This is an analysis of the error."
                assert solution == "This is a proposed solution."
                
                # Verify OpenAI client was created with correct API key
                mock_openai.assert_called_once_with(api_key='fake-api-key')
                
                # Verify OpenAI completion was called with correct parameters
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args['model'] == "gpt-4"
                assert len(call_args['messages']) == 2
                assert call_args['messages'][0]['role'] == "system"
                assert call_args['messages'][1]['role'] == "user"
                assert "Some AWS S3 permission error" in call_args['messages'][1]['content']

def test_ai_help_response_without_solution_section(app):
    """Test get_ai_help with a response that doesn't have a Solution section"""
    with app.app_context():
        # Mock SettingORM.get to return appropriate values
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            def mock_get_side_effect(key, default=None):
                if key == 'enable_ai_help':
                    return 'true'
                if key == 'openai_api_key':
                    return 'fake-api-key'
                return default
            
            mock_get.side_effect = mock_get_side_effect
            
            # Mock OpenAI client and response without Solution section
            mock_client = MagicMock()
            mock_response = MockOpenAIResponse("Analysis: This is an analysis of the error. This is the second sentence that should be used as solution.")
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock OpenAI.OpenAI to return mock_client
            with patch('app.utils.ai_helper.openai.OpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                # Call get_ai_help
                analysis, solution = get_ai_help("Some error output")
                
                # Verify analysis is extracted and solution is the second sentence
                assert "This is an analysis of the error" in analysis
                assert "This is the second sentence that should be used as solution" in solution

def test_ai_help_api_error(app):
    """Test get_ai_help when OpenAI API raises an exception"""
    with app.app_context():
        # Mock SettingORM.get to return appropriate values
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            def mock_get_side_effect(key, default=None):
                if key == 'enable_ai_help':
                    return 'true'
                if key == 'openai_api_key':
                    return 'fake-api-key'
                return default
            
            mock_get.side_effect = mock_get_side_effect
            
            # Mock OpenAI client to raise an exception
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
            
            # Mock OpenAI.OpenAI to return mock_client
            with patch('app.utils.ai_helper.openai.OpenAI') as mock_openai, \
                 patch('app.utils.ai_helper.logger') as mock_logger:
                mock_openai.return_value = mock_client
                
                # Call get_ai_help
                analysis, solution = get_ai_help("Some error output")
                
                # Verify error message is returned
                assert "Error getting AI help" in analysis
                assert "API rate limit exceeded" in analysis
                assert solution is None
                
                # Verify logger.error was called
                mock_logger.error.assert_called_once()
                assert "API rate limit exceeded" in mock_logger.error.call_args[0][0]

def test_ai_help_single_sentence_response(app):
    """Test get_ai_help when the response is a single sentence without a period"""
    with app.app_context():
        # Mock SettingORM.get to return appropriate values
        with patch('app.utils.ai_helper.SettingORM.get') as mock_get:
            def mock_get_side_effect(key, default=None):
                if key == 'enable_ai_help':
                    return 'true'
                if key == 'openai_api_key':
                    return 'fake-api-key'
                return default
            
            mock_get.side_effect = mock_get_side_effect
            
            # Mock OpenAI client and response with single sentence
            mock_client = MagicMock()
            mock_response = MockOpenAIResponse("Analysis: This is just a single sentence analysis without a period")
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock OpenAI.OpenAI to return mock_client
            with patch('app.utils.ai_helper.openai.OpenAI') as mock_openai:
                mock_openai.return_value = mock_client
                
                # Call get_ai_help
                analysis, solution = get_ai_help("Some error output")
                
                # Verify analysis and solution are extracted correctly
                assert "This is just a single sentence analysis without a period" in analysis
                assert solution == "No solution provided."