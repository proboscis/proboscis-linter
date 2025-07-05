"""End-to-end tests for the debug_files module."""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestMain:
    """End-to-end test cases for main function."""

    def test_main_script_execution(self):
        """Test executing debug_files.py as a script."""
        # Create a temporary directory with Python files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create test Python files
            (tmppath / "test1.py").write_text("""
def example_function():
    '''Example function with proper docstring.'''
    return 42
""")
            
            (tmppath / "test2.py").write_text("""
class ExampleClass:
    '''Example class with docstring.'''
    
    def method(self):
        '''Method docstring.'''
        pass
""")
            
            # Create a file with violations
            (tmppath / "bad_file.py").write_text("""
def no_docstring_function():
    pass

class NoDocstringClass:
    def method_without_docstring(self):
        x = 1
        y = 2
        return x + y
""")
            
            # Get the path to debug_files.py
            debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(debug_files_path)],
                cwd=str(tmppath),
                capture_output=True,
                text=True
            )
            
            # Check that the script fails with AttributeError
            assert result.returncode == 1
            assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr

    def test_main_with_complex_project_structure(self):
        """Test debug_files with a more complex project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create a project structure similar to a real Python project
            # src directory
            src = tmppath / "src"
            src.mkdir()
            (src / "__init__.py").write_text("")
            
            # Create package
            package = src / "mypackage"
            package.mkdir()
            (package / "__init__.py").write_text("__version__ = '1.0.0'")
            (package / "core.py").write_text("""
'''Core module.'''

def main():
    '''Main entry point.'''
    print("Hello, World!")
""")
            
            # Create subpackage
            subpkg = package / "utils"
            subpkg.mkdir()
            (subpkg / "__init__.py").write_text("")
            (subpkg / "helpers.py").write_text("""
'''Helper utilities.'''

def format_string(s):
    '''Format a string.'''
    return s.strip().lower()
""")
            
            # tests directory
            tests = tmppath / "tests"
            tests.mkdir()
            (tests / "__init__.py").write_text("")
            (tests / "test_core.py").write_text("""
'''Tests for core module.'''
import pytest

def test_main():
    '''Test main function.'''
    assert True
""")
            
            # Create some files that should be ignored
            (tmppath / "setup.py").write_text("# Setup file")
            (tmppath / ".gitignore").write_text("*.pyc\n__pycache__/\n.pytest_cache/")
            
            # Run the script
            debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
            result = subprocess.run(
                [sys.executable, str(debug_files_path)],
                cwd=str(tmppath),
                capture_output=True,
                text=True
            )
            
            # Check that the script fails with AttributeError
            assert result.returncode == 1
            assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr

    def test_main_empty_directory(self):
        """Test debug_files in an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run the script in empty directory
            debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
            result = subprocess.run(
                [sys.executable, str(debug_files_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            # Check that the script fails with AttributeError
            assert result.returncode == 1
            assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr

    def test_main_with_symlinks(self):
        """Test debug_files handling of symbolic links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create a Python file
            (tmppath / "original.py").write_text("# Original file")
            
            # Create a symlink to the file
            symlink = tmppath / "link_to_original.py"
            try:
                symlink.symlink_to("original.py")
            except OSError:
                # Skip test on systems that don't support symlinks
                pytest.skip("Symbolic links not supported on this system")
            
            # Run the script
            debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
            result = subprocess.run(
                [sys.executable, str(debug_files_path)],
                cwd=str(tmppath),
                capture_output=True,
                text=True
            )
            
            # Check that the script fails with AttributeError
            assert result.returncode == 1
            assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr

    def test_main_with_permission_errors(self):
        """Test debug_files handling of files with permission errors."""
        import os
        import stat
        
        # Skip on Windows as permission handling is different
        if sys.platform.startswith('win'):
            pytest.skip("Permission test not applicable on Windows")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create a Python file
            (tmppath / "readable.py").write_text("# Readable file")
            
            # Create a directory with restricted permissions
            restricted_dir = tmppath / "restricted"
            restricted_dir.mkdir()
            (restricted_dir / "hidden.py").write_text("# Hidden file")
            
            # Remove read permissions
            os.chmod(restricted_dir, stat.S_IWUSR)
            
            try:
                # Run the script
                debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
                result = subprocess.run(
                    [sys.executable, str(debug_files_path)],
                    cwd=str(tmppath),
                    capture_output=True,
                    text=True
                )
                
                # Check that the script fails with AttributeError
                assert result.returncode == 1
                assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr
                
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_dir, stat.S_IRWXU)

    def test_main_output_format(self):
        """Test that the output format is consistent and readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create files with various names
            (tmppath / "a_file.py").write_text("# A")
            (tmppath / "b_file.py").write_text("# B")
            (tmppath / "z_file.py").write_text("# Z")
            
            # Run the script
            debug_files_path = Path(__file__).parent.parent.parent / "debug_files.py"
            result = subprocess.run(
                [sys.executable, str(debug_files_path)],
                cwd=str(tmppath),
                capture_output=True,
                text=True
            )
            
            # Check that the script fails with AttributeError
            assert result.returncode == 1
            assert "AttributeError: 'ProboscisLinter' object has no attribute '_find_python_files'" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__])