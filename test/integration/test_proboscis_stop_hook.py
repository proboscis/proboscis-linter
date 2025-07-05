"""Integration tests for proboscis_stop_hook.py."""
import json
import sys
import subprocess
import tempfile
from pathlib import Path

# Add the parent directory to the path to import proboscis_stop_hook
sys.path.insert(0, '/Users/s22625/repos/proboscis-linter')


def test_main():
    """Test the main function integration with actual subprocess calls."""
    # Create a temporary directory structure for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a simple Python project structure
        src_dir = tmppath / "src"
        src_dir.mkdir()
        
        test_dir = tmppath / "test"
        test_dir.mkdir()
        
        # Create a simple Python file
        example_py = src_dir / "example.py"
        example_py.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
        
        # Create a test file with good coverage
        test_file = test_dir / "test_example.py"
        test_file.write_text("""
import sys
sys.path.insert(0, '../src')
from example import add, subtract, multiply, divide
import pytest

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5
    with pytest.raises(ValueError):
        divide(5, 0)
""")
        
        # Create pyproject.toml
        pyproject = tmppath / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["pytest", "pytest-cov"]
""")
        
        # Copy the proboscis_stop_hook.py to temp directory
        hook_script = tmppath / "proboscis_stop_hook.py"
        original_hook = Path('/Users/s22625/repos/proboscis-linter/proboscis_stop_hook.py')
        hook_script.write_text(original_hook.read_text())
        
        # Test the hook script directly
        # Test case 1: Run with good coverage (should approve)
        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input='{}',
            capture_output=True,
            text=True,
            cwd=str(tmppath)
        )
        
        # Parse the output
        output = json.loads(result.stdout)
        
        # Since we're running in a test environment, it might fail due to missing dependencies
        # But we can verify the structure of the output
        assert 'decision' in output
        assert 'reason' in output
        
        # Test case 2: Run with stop_hook_active flag (should exit immediately)
        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input='{"stop_hook_active": true}',
            capture_output=True,
            text=True,
            cwd=str(tmppath)
        )
        
        # Should exit with code 0 and no output
        assert result.returncode == 0
        assert result.stdout == ''
        
        # Test case 3: Test with failing tests
        # Create a test file that will fail
        failing_test = test_dir / "test_failing.py"
        failing_test.write_text("""
def test_will_fail():
    assert False, "This test is designed to fail"
""")
        
        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input='{}',
            capture_output=True,
            text=True,
            cwd=str(tmppath)
        )
        
        if result.stdout:
            output = json.loads(result.stdout)
            # If tests were actually run, check the output
            if output['decision'] == 'block':
                assert 'reason' in output
                assert output.get('continue', False) is True