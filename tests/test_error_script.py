import pytest
import os
import sys
import importlib.util
from unittest.mock import patch, MagicMock

# Mock boto3 as it might not be available in the environment
mock_boto3 = MagicMock()
mock_boto3.exceptions = MagicMock()
mock_boto3.exceptions.Boto3Error = Exception

# Get the path to the error_test.py script
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'error_test.py')

def test_script_can_be_imported():
    """Test that error_test.py script can be imported"""
    # Dynamic script import
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        spec = importlib.util.spec_from_file_location("error_test", SCRIPT_PATH)
        error_test = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(error_test)
    
    # Check that the script has a main function
    assert hasattr(error_test, 'main')
    assert callable(error_test.main)

def test_main_function_returns_error_code():
    """Test that main function returns error code on exception"""
    # Import the script
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        spec = importlib.util.spec_from_file_location("error_test", SCRIPT_PATH)
        error_test = importlib.util.module_from_spec(spec)
        
        # Mock boto3.client to generate an exception
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = Exception("Bucket does not exist")
        mock_boto3.client.return_value = mock_s3
        
        # Load the module with boto3 patch
        spec.loader.exec_module(error_test)
        
        with patch('sys.stderr'):  # Suppress error output to stderr
            # Call main and check return code
            return_code = error_test.main()
            assert return_code == 1  # Expect error code 1

def test_error_handling_output():
    """Test that errors are correctly output to stderr"""
    # Import the script
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        spec = importlib.util.spec_from_file_location("error_test", SCRIPT_PATH)
        error_test = importlib.util.module_from_spec(spec)
        
        # Mock boto3.client to generate an exception
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = Exception("Bucket does not exist")
        mock_boto3.client.return_value = mock_s3
        
        # Load the module with boto3 patch
        spec.loader.exec_module(error_test)
        
        with patch('sys.stdout') as mock_stdout, patch('sys.stderr') as mock_stderr:
            # Call main
            error_test.main()
            
            # Check output in stdout and stderr
            stdout_output = ''.join([call[0][0] for call in mock_stdout.write.call_args_list if call[0]])
            stderr_output = ''.join([call[0][0] for call in mock_stderr.write.call_args_list if call[0]])
            
            assert "Starting error test script" in stdout_output
            assert "Attempting to access non-existent bucket" in stdout_output
            assert "Error occurred: Bucket does not exist" in stderr_output
            assert "This line should never be reached" not in stdout_output

def test_successful_execution():
    """Test that main function returns 0 on successful execution"""
    # Import the script
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        spec = importlib.util.spec_from_file_location("error_test", SCRIPT_PATH)
        error_test = importlib.util.module_from_spec(spec)
        
        # Mock boto3.client for successful execution
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {'Body': 'content'}
        mock_boto3.client.return_value = mock_s3
        
        # Load the module with boto3 patch
        spec.loader.exec_module(error_test)
        
        with patch('sys.stdout') as mock_stdout:
            # Call main
            return_code = error_test.main()
            
            # Check return code and output
            assert return_code == 0
            stdout_output = ''.join([call[0][0] for call in mock_stdout.write.call_args_list if call[0]])
            assert "Starting error test script" in stdout_output
            assert "Attempting to access non-existent bucket" in stdout_output
            assert "This line should never be reached" in stdout_output

def test_exception_details():
    """Test various exception types and their output"""
    # Import the script
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        spec = importlib.util.spec_from_file_location("error_test", SCRIPT_PATH)
        error_test = importlib.util.module_from_spec(spec)
        
        # List of different exceptions for testing
        exceptions = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            ConnectionError("Cannot connect to AWS"),
            Exception("Boto3 specific error")
        ]
        
        # Load the module with boto3 patch
        spec.loader.exec_module(error_test)
        
        for exception in exceptions:
            # Mock boto3.client to generate different exceptions
            mock_s3 = MagicMock()
            mock_s3.get_object.side_effect = exception
            mock_boto3.client.return_value = mock_s3
            
            with patch('sys.stderr') as mock_stderr:
                # Call main
                return_code = error_test.main()
                
                # Check return code and stderr output
                assert return_code == 1
                stderr_output = ''.join([call[0][0] for call in mock_stderr.write.call_args_list if call[0]])
                assert f"Error occurred: {str(exception)}" in stderr_output

if __name__ == "__main__":
    pytest.main(['-xvs', __file__])