"""Integration tests for rust_linter module."""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig, RuleConfig


@pytest.mark.integration
def test_RustLinterWrapper_lint_project():
    """Integration test for RustLinterWrapper.lint_project method."""
    config = ProboscisConfig()
    
    with patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True):
        with patch('proboscis_linter.rust_linter.proboscis_linter_rust') as mock_rust_module:
            mock_rust_linter = Mock()
            mock_rust_module.RustLinter.return_value = mock_rust_linter
            
            # Create mock violations
            mock_violation = Mock()
            mock_violation.rule_name = "PL001:require-unit-test"
            mock_violation.file_path = "/test/file.py"
            mock_violation.line_number = 10
            mock_violation.function_name = "test_func"
            mock_violation.message = "Missing unit test"
            mock_violation.severity = "error"
            
            mock_rust_linter.lint_project.return_value = [mock_violation]
            
            wrapper = RustLinterWrapper(config)
            violations = wrapper.lint_project(Path("/test/project"))
            
            assert len(violations) == 1
            assert violations[0].rule_name == "PL001:require-unit-test"
            mock_rust_linter.lint_project.assert_called_once()


@pytest.mark.integration
def test_RustLinterWrapper_lint_file():
    """Integration test for RustLinterWrapper.lint_file method."""
    config = ProboscisConfig()
    
    with patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True):
        with patch('proboscis_linter.rust_linter.proboscis_linter_rust') as mock_rust_module:
            mock_rust_linter = Mock()
            mock_rust_module.RustLinter.return_value = mock_rust_linter
            
            # Create mock violations
            mock_violation = Mock()
            mock_violation.rule_name = "PL002:require-integration-test"
            mock_violation.file_path = "/test/file.py"
            mock_violation.line_number = 20
            mock_violation.function_name = "test_func"
            mock_violation.message = "Missing integration test"
            mock_violation.severity = "error"
            
            mock_rust_linter.lint_file.return_value = [mock_violation]
            
            wrapper = RustLinterWrapper(config)
            violations = wrapper.lint_file(Path("/test/file.py"), [Path("/test")])
            
            assert len(violations) == 1
            assert violations[0].rule_name == "PL002:require-integration-test"
            mock_rust_linter.lint_file.assert_called_once()


@pytest.mark.integration
def test_RustLinterWrapper_lint_changed_files():
    """Integration test for RustLinterWrapper.lint_changed_files method."""
    config = ProboscisConfig()
    
    with patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True):
        with patch('proboscis_linter.rust_linter.proboscis_linter_rust') as mock_rust_module:
            mock_rust_linter = Mock()
            mock_rust_module.RustLinter.return_value = mock_rust_linter
            
            # Create mock violations
            mock_violation = Mock()
            mock_violation.rule_name = "PL003:require-e2e-test"
            mock_violation.file_path = "/test/changed.py"
            mock_violation.line_number = 30
            mock_violation.function_name = "test_func"
            mock_violation.message = "Missing e2e test"
            mock_violation.severity = "error"
            
            mock_rust_linter.lint_changed_files.return_value = [mock_violation]
            
            wrapper = RustLinterWrapper(config)
            violations = wrapper.lint_changed_files(Path("/test/project"))
            
            assert len(violations) == 1
            assert violations[0].rule_name == "PL003:require-e2e-test"
            mock_rust_linter.lint_changed_files.assert_called_once()


class TestRustLinterIntegration:
    """Integration tests for RustLinterWrapper."""
    
    @pytest.mark.integration
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_project_with_custom_config(self, mock_rust_module):
        """Test linting project with custom configuration."""
        # Setup custom config
        config = ProboscisConfig(
            test_directories=["custom_tests", "tests"],
            test_patterns=["*_test.py", "test_*.py"],
            exclude_patterns=["**/vendor/**", "**/__pycache__/**"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=True)
            }
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create multiple mock violations
        violations_data = [
            ("PL001:require-unit-test", "/src/module1.py", 10, "func1", "Missing unit test", "error"),
            ("PL002:require-integration-test", "/src/module2.py", 20, "func2", "Missing integration test", "error"),
            ("PL003:require-e2e-test", "/src/module3.py", 30, "func3", "Missing e2e test", "error"),
            ("PL001:require-unit-test", "/src/module4.py", 40, "func4", "Missing unit test", "error"),
        ]
        
        mock_violations = []
        for rule, path, line, func, msg, sev in violations_data:
            mock_violation = Mock()
            mock_violation.rule_name = rule
            mock_violation.file_path = path
            mock_violation.line_number = line
            mock_violation.function_name = func
            mock_violation.message = msg
            mock_violation.severity = sev
            mock_violations.append(mock_violation)
        
        mock_rust_linter.lint_project.return_value = mock_violations
        
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(Path("/test/project"))
        
        # Verify only enabled rules are returned
        assert len(violations) == 3  # PL002 is disabled
        rule_names = [v.rule_name for v in violations]
        assert "PL002:require-integration-test" not in rule_names
        assert rule_names.count("PL001:require-unit-test") == 2
        assert "PL003:require-e2e-test" in rule_names
    
    @pytest.mark.integration
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_file_integration(self, mock_rust_module):
        """Test linting a single file with multiple violations."""
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create violations for different rules
        violations_data = [
            ("PL001:require-unit-test", "/src/utils.py", 5, "helper_func", "Missing unit test", "error"),
            ("PL002:require-integration-test", "/src/utils.py", 5, "helper_func", "Missing integration test", "error"),
            ("PL003:require-e2e-test", "/src/utils.py", 5, "helper_func", "Missing e2e test", "error"),
        ]
        
        mock_violations = []
        for rule, path, line, func, msg, sev in violations_data:
            mock_violation = Mock()
            mock_violation.rule_name = rule
            mock_violation.file_path = path
            mock_violation.line_number = line
            mock_violation.function_name = func
            mock_violation.message = msg
            mock_violation.severity = sev
            mock_violations.append(mock_violation)
        
        mock_rust_linter.lint_file.return_value = mock_violations
        
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_file(Path("/src/utils.py"), [Path("/test")])
        
        # Verify all violations are returned
        assert len(violations) == 3
        assert all(v.file_path == Path("/src/utils.py") for v in violations)
        assert all(v.function_name == "helper_func" for v in violations)
        assert all(v.line_number == 5 for v in violations)
        
        # Check each rule type
        rule_names = {v.rule_name for v in violations}
        assert rule_names == {
            "PL001:require-unit-test",
            "PL002:require-integration-test",
            "PL003:require-e2e-test"
        }
    
    @pytest.mark.integration
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_lint_changed_files_with_mixed_results(self, mock_rust_module):
        """Test linting changed files with a mix of violations and clean files."""
        config = ProboscisConfig(
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=True),
                "PL003": RuleConfig(enabled=False)  # Disabled
            }
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create violations for changed files
        violations_data = [
            ("PL001:require-unit-test", "/src/changed1.py", 10, "new_func", "Missing unit test", "error"),
            ("PL002:require-integration-test", "/src/changed1.py", 10, "new_func", "Missing integration test", "error"),
            ("PL003:require-e2e-test", "/src/changed2.py", 20, "modified_func", "Missing e2e test", "error"),
            ("PL001:require-unit-test", "/src/changed3.py", 30, "added_func", "Missing unit test", "error"),
        ]
        
        mock_violations = []
        for rule, path, line, func, msg, sev in violations_data:
            mock_violation = Mock()
            mock_violation.rule_name = rule
            mock_violation.file_path = path
            mock_violation.line_number = line
            mock_violation.function_name = func
            mock_violation.message = msg
            mock_violation.severity = sev
            mock_violations.append(mock_violation)
        
        mock_rust_linter.lint_changed_files.return_value = mock_violations
        
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_changed_files(Path("/test/project"))
        
        # Verify filtering works correctly
        assert len(violations) == 3  # PL003 is disabled
        
        # Check that PL003 violation was filtered out
        rule_names = [v.rule_name for v in violations]
        assert "PL003:require-e2e-test" not in rule_names
        
        # Verify the remaining violations
        file_paths = {str(v.file_path) for v in violations}
        assert file_paths == {"/src/changed1.py", "/src/changed3.py"}
    
    @pytest.mark.integration
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_error_handling_in_lint_operations(self, mock_rust_module):
        """Test error handling when Rust linter operations fail."""
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Test lint_project error
        mock_rust_linter.lint_project.side_effect = RuntimeError("Rust linter crashed")
        
        wrapper = RustLinterWrapper(config)
        
        with pytest.raises(RuntimeError, match="Rust linter crashed"):
            wrapper.lint_project(Path("/test/project"))
        
        # Test lint_file error
        mock_rust_linter.lint_file.side_effect = ValueError("Invalid file path")
        
        with pytest.raises(ValueError, match="Invalid file path"):
            wrapper.lint_file(Path("/invalid/file.py"), [Path("/test")])
        
        # Test lint_changed_files error
        mock_rust_linter.lint_changed_files.side_effect = OSError("Git command failed")
        
        with pytest.raises(OSError, match="Git command failed"):
            wrapper.lint_changed_files(Path("/test/project"))
    
    @pytest.mark.integration
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_complex_rule_filtering_scenario(self, mock_rust_module):
        """Test complex scenario with multiple rule configurations."""
        # Create config with various rule states
        config = ProboscisConfig(
            rules={
                "PL001": RuleConfig(enabled=True, options={"strict": True}),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=True),
                # PL004 not configured - should default to enabled
            }
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create violations for all rule types
        violations_data = [
            ("PL001:require-unit-test", "/src/file1.py", 10, "func1", "Missing unit test", "error"),
            ("PL002:require-integration-test", "/src/file2.py", 20, "func2", "Missing integration test", "error"),
            ("PL003:require-e2e-test", "/src/file3.py", 30, "func3", "Missing e2e test", "error"),
            ("PL004:custom-rule", "/src/file4.py", 40, "func4", "Custom violation", "warning"),
            ("PL001:require-unit-test", "/src/file5.py", 50, "func5", "Missing unit test", "error"),
        ]
        
        mock_violations = []
        for rule, path, line, func, msg, sev in violations_data:
            mock_violation = Mock()
            mock_violation.rule_name = rule
            mock_violation.file_path = path
            mock_violation.line_number = line
            mock_violation.function_name = func
            mock_violation.message = msg
            mock_violation.severity = sev
            mock_violations.append(mock_violation)
        
        mock_rust_linter.lint_project.return_value = mock_violations
        
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(Path("/test/project"))
        
        # Verify filtering
        assert len(violations) == 4  # PL002 is disabled
        
        rule_names = [v.rule_name for v in violations]
        assert "PL002:require-integration-test" not in rule_names
        assert rule_names.count("PL001:require-unit-test") == 2
        assert "PL003:require-e2e-test" in rule_names
        assert "PL004:custom-rule" in rule_names  # Not configured, defaults to enabled