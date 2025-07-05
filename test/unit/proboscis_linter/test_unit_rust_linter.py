"""Unit tests for rust_linter module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from proboscis_linter.rust_linter import RustLinterWrapper, RUST_AVAILABLE
from proboscis_linter.config import ProboscisConfig
from proboscis_linter.models import LintViolation


class TestRustLinterWrapper:
    """Test RustLinterWrapper class."""
    
    def test_init_without_rust_extension(self):
        """Test initialization when Rust extension is not available."""
        with patch('proboscis_linter.rust_linter.RUST_AVAILABLE', False):
            config = ProboscisConfig()
            with pytest.raises(ImportError, match="Rust extension not built"):
                RustLinterWrapper(config)
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_init_with_rust_extension(self, mock_rust_module):
        """Test initialization when Rust extension is available."""
        config = ProboscisConfig(
            test_directories=["test", "tests"],
            test_patterns=["test_*.py"],
            exclude_patterns=["*.pyc"]
        )
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        wrapper = RustLinterWrapper(config)
        
        mock_rust_module.RustLinter.assert_called_once_with(
            test_directories=["test", "tests"],
            test_patterns=["test_*.py"],
            exclude_patterns=["*.pyc"]
        )
        assert wrapper._rust_linter == mock_rust_linter
        assert wrapper._config == config
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_project(self, mock_rust_module):
        """Test lint_project method."""
        # Setup
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create mock violation from Rust
        mock_rust_violation = Mock()
        mock_rust_violation.rule_name = "PL001:require-unit-test"
        mock_rust_violation.file_path = "/path/to/file.py"
        mock_rust_violation.line_number = 10
        mock_rust_violation.function_name = "test_function"
        mock_rust_violation.message = "Missing unit test"
        mock_rust_violation.severity = "error"
        
        mock_rust_linter.lint_project.return_value = [mock_rust_violation]
        
        wrapper = RustLinterWrapper(config)
        project_root = Path("/test/project")
        
        # Execute
        violations = wrapper.lint_project(project_root)
        
        # Verify
        mock_rust_linter.lint_project.assert_called_once_with("/test/project")
        assert len(violations) == 1
        assert isinstance(violations[0], LintViolation)
        assert violations[0].rule_name == "PL001:require-unit-test"
        assert violations[0].file_path == Path("/path/to/file.py")
        assert violations[0].line_number == 10
        assert violations[0].function_name == "test_function"
        assert violations[0].message == "Missing unit test"
        assert violations[0].severity == "error"
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_project_filters_disabled_rules(self, mock_rust_module):
        """Test that lint_project filters out disabled rules."""
        # Setup
        config = ProboscisConfig(rules={"PL001": {"enabled": False}})
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create mock violations
        mock_violation1 = Mock()
        mock_violation1.rule_name = "PL001:require-unit-test"
        mock_violation1.file_path = "/path/to/file1.py"
        mock_violation1.line_number = 10
        mock_violation1.function_name = "test_function1"
        mock_violation1.message = "Missing unit test"
        mock_violation1.severity = "error"
        
        mock_violation2 = Mock()
        mock_violation2.rule_name = "PL002:require-integration-test"
        mock_violation2.file_path = "/path/to/file2.py"
        mock_violation2.line_number = 20
        mock_violation2.function_name = "test_function2"
        mock_violation2.message = "Missing integration test"
        mock_violation2.severity = "error"
        
        mock_rust_linter.lint_project.return_value = [mock_violation1, mock_violation2]
        
        wrapper = RustLinterWrapper(config)
        project_root = Path("/test/project")
        
        # Execute
        violations = wrapper.lint_project(project_root)
        
        # Verify - only PL002 should be included
        assert len(violations) == 1
        assert violations[0].rule_name == "PL002:require-integration-test"
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_file(self, mock_rust_module):
        """Test lint_file method."""
        # Setup
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create mock violation
        mock_rust_violation = Mock()
        mock_rust_violation.rule_name = "PL001:require-unit-test"
        mock_rust_violation.file_path = "/path/to/file.py"
        mock_rust_violation.line_number = 10
        mock_rust_violation.function_name = "test_function"
        mock_rust_violation.message = "Missing unit test"
        mock_rust_violation.severity = "error"
        
        mock_rust_linter.lint_file.return_value = [mock_rust_violation]
        
        wrapper = RustLinterWrapper(config)
        file_path = Path("/path/to/file.py")
        test_dirs = [Path("/test")]
        
        # Execute
        violations = wrapper.lint_file(file_path, test_dirs)
        
        # Verify
        mock_rust_linter.lint_file.assert_called_once_with("/path/to/file.py")
        assert len(violations) == 1
        assert isinstance(violations[0], LintViolation)
        assert violations[0].rule_name == "PL001:require-unit-test"
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_changed_files(self, mock_rust_module):
        """Test lint_changed_files method."""
        # Setup
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create mock violations
        mock_rust_violation = Mock()
        mock_rust_violation.rule_name = "PL001:require-unit-test"
        mock_rust_violation.file_path = "/path/to/changed.py"
        mock_rust_violation.line_number = 15
        mock_rust_violation.function_name = "changed_function"
        mock_rust_violation.message = "Missing unit test"
        mock_rust_violation.severity = "error"
        
        mock_rust_linter.lint_changed_files.return_value = [mock_rust_violation]
        
        wrapper = RustLinterWrapper(config)
        project_root = Path("/test/project")
        
        # Execute
        violations = wrapper.lint_changed_files(project_root)
        
        # Verify
        mock_rust_linter.lint_changed_files.assert_called_once_with("/test/project")
        assert len(violations) == 1
        assert isinstance(violations[0], LintViolation)
        assert violations[0].file_path == Path("/path/to/changed.py")
        assert violations[0].function_name == "changed_function"
    
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_empty_violations(self, mock_rust_module):
        """Test handling of empty violations list."""
        # Setup
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        mock_rust_linter.lint_project.return_value = []
        
        wrapper = RustLinterWrapper(config)
        project_root = Path("/test/project")
        
        # Execute
        violations = wrapper.lint_project(project_root)
        
        # Verify
        assert violations == []