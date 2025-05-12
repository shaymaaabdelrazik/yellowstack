import pytest
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock

# Get the path to the test_params.py script
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'test_params.py')

def test_script_imports():
    """Check that the script can be imported"""
    # Import the module
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_params", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Check that the main function exists
    assert hasattr(module, 'main')
    assert callable(module.main)

def test_argparse_configuration():
    """Test that command line arguments are configured correctly"""
    # Run the script with --help to get usage information
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "--help"],
        capture_output=True,
        text=True
    )
    
    # Check that the program exited successfully and contains descriptions of all parameters
    assert result.returncode == 0
    assert '--name' in result.stdout
    assert '--age' in result.stdout
    assert '--verbose' in result.stdout
    assert '--delay' in result.stdout

def test_script_with_parameters():
    """Test script execution with various parameters"""
    # Run the script with parameters
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, '--name', 'Alice', '--age', '30', '--verbose'],
        capture_output=True,
        text=True
    )
    
    # Check the output
    assert result.returncode == 0
    assert 'name: Alice' in result.stdout
    assert 'age: 30' in result.stdout
    assert 'verbose: True' in result.stdout
    assert 'Hello, Alice, you are 30 years old!' in result.stdout
    assert 'Verbose output mode enabled' in result.stdout

def test_script_with_delay():
    """Test script execution with delay parameter"""
    # Run the script directly but with a small delay value
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, '--name', 'Bob', '--delay', '1'],
        capture_output=True,
        text=True,
        timeout=5  # Limit execution time to 5 seconds
    )
    
    # Check the output
    assert result.returncode == 0
    assert 'name: Bob' in result.stdout
    assert 'delay: 1' in result.stdout
    assert 'Waiting for 1 seconds' in result.stdout
    assert 'remaining' in result.stdout

def test_script_without_parameters():
    """Test script execution without parameters"""
    # Run the script without parameters
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH],
        capture_output=True,
        text=True
    )
    
    # Check the output
    assert result.returncode == 0
    assert 'name: None' in result.stdout
    assert 'age: None' in result.stdout
    assert 'verbose: False' in result.stdout
    assert 'delay: 0' in result.stdout
    assert 'Script completed successfully!' in result.stdout
    # There should be no greeting without a name
    assert 'Hello' not in result.stdout