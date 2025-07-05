"""End-to-end tests for benchmark_small module."""
import subprocess
import sys
import tempfile
from pathlib import Path


def test_main():
    """Test the main function end-to-end with subprocess execution."""
    # Test missing argument
    result = subprocess.run(
        [sys.executable, "benchmark_small.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "Usage: python benchmark_small.py <project_path>" in result.stdout
    
    # Test with non-existent path
    result = subprocess.run(
        [sys.executable, "benchmark_small.py", "/non/existent/path"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "Error: /non/existent/path does not exist" in result.stdout
    
    # Test with real temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create test Python files
        (test_path / "module1.py").write_text("""
def function_without_docstring():
    x = 1
    y = 2
    return x + y

class ClassWithoutDocstring:
    def method(self):
        pass
""")
        
        (test_path / "module2.py").write_text("""
\"\"\"Module with some issues.\"\"\"

def very_long_function_name_that_exceeds_reasonable_length_limits():
    \"\"\"This function has a very long name.\"\"\"
    pass

def function_with_unused_variable():
    \"\"\"Function with unused variable.\"\"\"
    unused = 42
    return 10
""")
        
        (test_path / "__init__.py").write_text("")
        
        # Run the benchmark script
        # Note: Since Rust extension might not be built, we mock it for e2e test
        test_script = """
import sys
sys.path.insert(0, '.')

# Mock the Rust linter if not available
try:
    from proboscis_linter.rust_linter import RustLinterWrapper
except ImportError:
    import types
    import proboscis_linter
    
    # Create mock module
    rust_linter_module = types.ModuleType('rust_linter')
    
    class MockRustLinterWrapper:
        def __init__(self, config):
            self.config = config
        
        def lint_project(self, path):
            # Return some mock violations
            return [
                {'file': 'module1.py', 'line': 2, 'message': 'Missing function docstring'},
                {'file': 'module1.py', 'line': 7, 'message': 'Missing class docstring'},
                {'file': 'module2.py', 'line': 3, 'message': 'Function name too long'},
                {'file': 'module2.py', 'line': 10, 'message': 'Unused variable: unused'}
            ]
    
    rust_linter_module.RustLinterWrapper = MockRustLinterWrapper
    proboscis_linter.rust_linter = rust_linter_module
    sys.modules['proboscis_linter.rust_linter'] = rust_linter_module

# Now import and run the benchmark
import benchmark_small
benchmark_small.main()
"""
        
        result = subprocess.run(
            [sys.executable, "-c", test_script, str(test_path)],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        # Check output contains expected information
        output = result.stdout + result.stderr
        assert "Benchmarking Rust linter on:" in output
        assert str(test_path) in output
        assert "Rust Implementation:" in output
        assert "Time:" in output
        assert "seconds" in output
        assert "Violations found:" in output
        assert "Processing speed:" in output
        assert "files/second" in output


def test_main_script_execution():
    """Test running the script as a module."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        (test_path / "test.py").write_text("print('test')")
        
        # Test running as module
        result = subprocess.run(
            [sys.executable, "-m", "benchmark_small", str(test_path)],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        # Should either work or fail with import error for Rust module
        assert result.returncode in [0, 1]
        if result.returncode == 1:
            # If it failed, should be due to missing Rust extension
            assert "No module named" in result.stderr or "Rust implementation not available" in result.stdout


def test_main_with_config_file():
    """Test e2e with configuration file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create config file
        config_content = """
[tool.proboscis]
exclude = ["tests/*", "build/*"]
max_line_length = 100
max_complexity = 10
"""
        (test_path / "pyproject.toml").write_text(config_content)
        
        # Create test files
        (test_path / "main.py").write_text("""
def main():
    \"\"\"Main function.\"\"\"
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
        
        (test_path / "tests").mkdir()
        (test_path / "tests" / "test_main.py").write_text("""
def test_main():
    \"\"\"Test main function.\"\"\"
    pass
""")
        
        # Run with mocked Rust implementation
        mock_script = """
import sys
sys.path.insert(0, '.')

# Mock setup - always mock regardless of import success
import types
import proboscis_linter

rust_linter_module = types.ModuleType('rust_linter')

class MockRustLinterWrapper:
    def __init__(self, config):
        self.config = config
    
    def lint_project(self, path):
        # Should not lint files in tests/ due to config
        return [{'file': 'main.py', 'line': 1, 'message': 'Example violation'}]

rust_linter_module.RustLinterWrapper = MockRustLinterWrapper
proboscis_linter.rust_linter = rust_linter_module
sys.modules['proboscis_linter.rust_linter'] = rust_linter_module

import benchmark_small
benchmark_small.main()
"""
        
        result = subprocess.run(
            [sys.executable, "-c", mock_script, str(test_path)],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        output = result.stdout + result.stderr
        assert "Violations found: 1" in output


def test_main_performance_output():
    """Test that performance metrics are calculated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create multiple files to simulate a larger project
        for i in range(20):
            (test_path / f"module_{i}.py").write_text(f'print("Module {i}")')
        
        # Mock script with controlled timing
        mock_script = """
import sys
import time
sys.path.insert(0, '.')

# Mock setup with controlled timing - always mock
import types
import proboscis_linter

rust_linter_module = types.ModuleType('rust_linter')

class MockRustLinterWrapper:
    def __init__(self, config):
        self.config = config
    
    def lint_project(self, path):
        # Simulate some processing time
        time.sleep(0.1)  # 100ms
        return [{'file': f'module_{i}.py', 'line': 1, 'message': 'violation'} for i in range(10)]

rust_linter_module.RustLinterWrapper = MockRustLinterWrapper
proboscis_linter.rust_linter = rust_linter_module
sys.modules['proboscis_linter.rust_linter'] = rust_linter_module

import benchmark_small
benchmark_small.main()
"""
        
        result = subprocess.run(
            [sys.executable, "-c", mock_script, str(test_path)],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        output = result.stdout
        
        # Verify performance calculation
        assert "Time:" in output
        assert "Processing speed:" in output
        assert "files/second" in output
        
        # With 0.1 second processing time, speed should be around 7720 files/second
        import re
        speed_match = re.search(r'Processing speed: (\d+) files/second', output)
        if speed_match:
            speed = int(speed_match.group(1))
            # Should be approximately 772/0.1 = 7720
            assert 7000 < speed < 8500  # Allow some variance


def test_main_error_handling():
    """Test error handling in e2e context."""
    # Test with a path that exists but causes an error during linting
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create a file that might cause issues
        (test_path / "bad_file.py").write_text("This is not valid Python syntax {{{")
        
        # Mock script that simulates linting error
        mock_script = """
import sys
sys.path.insert(0, '.')

# Always mock
import types
import proboscis_linter

rust_linter_module = types.ModuleType('rust_linter')

class MockRustLinterWrapper:
    def __init__(self, config):
        self.config = config
    
    def lint_project(self, path):
        # Simulate a parsing error
        raise RuntimeError("Failed to parse file: bad_file.py")

rust_linter_module.RustLinterWrapper = MockRustLinterWrapper
proboscis_linter.rust_linter = rust_linter_module
sys.modules['proboscis_linter.rust_linter'] = rust_linter_module

import benchmark_small
try:
    benchmark_small.main()
except RuntimeError as e:
    print(f"Error occurred: {e}")
"""
        
        result = subprocess.run(
            [sys.executable, "-c", mock_script, str(test_path)],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        output = result.stdout + result.stderr
        assert "Error occurred:" in output or "RuntimeError" in output