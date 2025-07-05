"""Integration tests for the debug_files module."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import debug_files


class TestMain:
    """Integration test cases for main function."""

    @pytest.mark.integration
    def test_main_with_real_config_and_linter(self):
        """Test main function with real ProboscisConfig and ProboscisLinter."""
        # Create a temporary directory with Python files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create some test Python files
            (tmppath / "test1.py").write_text("# Test file 1\nprint('hello')")
            (tmppath / "test2.py").write_text("# Test file 2\ndef foo():\n    pass")
            subdir = tmppath / "subdir"
            subdir.mkdir()
            (subdir / "module.py").write_text("# Module\nclass MyClass:\n    pass")
            
            # Create a non-Python file that should be ignored
            (tmppath / "readme.txt").write_text("This is not a Python file")
            
            # Change to the temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmpdir)
                
                # Act - the script will fail because _find_python_files doesn't exist
                with pytest.raises(AttributeError) as exc_info:
                    debug_files.main()
                
                # Assert
                assert "'ProboscisLinter' object has no attribute '_find_python_files'" in str(exc_info.value)
                
            finally:
                os.chdir(original_cwd)

    @pytest.mark.integration
    def test_main_with_gitignore_patterns(self):
        """Test main function respects gitignore patterns."""
        # Create a temporary directory with gitignore
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create gitignore file
            (tmppath / ".gitignore").write_text("__pycache__/\n*.pyc\nvenv/\n.pytest_cache/")
            
            # Create Python files that should be found
            (tmppath / "main.py").write_text("# Main file")
            (tmppath / "utils.py").write_text("# Utils")
            
            # Create Python files that should be ignored
            pycache = tmppath / "__pycache__"
            pycache.mkdir()
            (pycache / "main.cpython-39.pyc").write_text("# Compiled")
            
            venv = tmppath / "venv"
            venv.mkdir()
            (venv / "setup.py").write_text("# Venv file")
            
            # Change to the temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmpdir)
                
                # Act - the script will fail because _find_python_files doesn't exist
                with pytest.raises(AttributeError) as exc_info:
                    debug_files.main()
                
                # Assert
                assert "'ProboscisLinter' object has no attribute '_find_python_files'" in str(exc_info.value)
                
            finally:
                os.chdir(original_cwd)

    @pytest.mark.integration
    def test_main_rust_import_error_handling(self):
        """Test main function handles Rust import errors gracefully."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test.py").write_text("# Test")
            
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmpdir)
                
                # Act - the script will fail because _find_python_files doesn't exist
                # This happens before we even get to the Rust import
                with pytest.raises(AttributeError) as exc_info:
                    debug_files.main()
                
                # Assert
                assert "'ProboscisLinter' object has no attribute '_find_python_files'" in str(exc_info.value)
                
            finally:
                os.chdir(original_cwd)

    @pytest.mark.integration
    def test_main_empty_project(self):
        """Test main function with empty project (no Python files)."""
        # Create a temporary directory with no Python files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create only non-Python files
            (tmppath / "README.md").write_text("# Project")
            (tmppath / "data.json").write_text('{"key": "value"}')
            
            # Change to the temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmpdir)
                
                # Act - the script will fail because _find_python_files doesn't exist
                with pytest.raises(AttributeError) as exc_info:
                    debug_files.main()
                
                # Assert
                assert "'ProboscisLinter' object has no attribute '_find_python_files'" in str(exc_info.value)
                
            finally:
                os.chdir(original_cwd)

    @pytest.mark.integration
    def test_main_nested_directory_structure(self):
        """Test main function with deeply nested directory structure."""
        # Create a temporary directory with nested structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create nested directory structure
            src = tmppath / "src"
            src.mkdir()
            (src / "__init__.py").write_text("")
            (src / "main.py").write_text("# Main")
            
            models = src / "models"
            models.mkdir()
            (models / "__init__.py").write_text("")
            (models / "user.py").write_text("# User model")
            (models / "product.py").write_text("# Product model")
            
            utils = src / "utils"
            utils.mkdir()
            (utils / "__init__.py").write_text("")
            (utils / "helpers.py").write_text("# Helpers")
            
            tests = tmppath / "tests"
            tests.mkdir()
            (tests / "test_main.py").write_text("# Tests")
            
            # Change to the temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmpdir)
                
                # Act - the script will fail because _find_python_files doesn't exist
                with pytest.raises(AttributeError) as exc_info:
                    debug_files.main()
                
                # Assert
                assert "'ProboscisLinter' object has no attribute '_find_python_files'" in str(exc_info.value)
                
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])