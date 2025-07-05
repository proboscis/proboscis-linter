"""End-to-end tests for rust_linter module."""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, Mock
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig


@pytest.mark.e2e
def test_RustLinterWrapper_lint_project():
    """E2E test for RustLinterWrapper.lint_project method."""
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
            assert violations[0].file_path == Path("/test/file.py")


@pytest.mark.e2e
def test_RustLinterWrapper_lint_file():
    """E2E test for RustLinterWrapper.lint_file method."""
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
            assert violations[0].file_path == Path("/test/file.py")


@pytest.mark.e2e
def test_RustLinterWrapper_lint_changed_files():
    """E2E test for RustLinterWrapper.lint_changed_files method."""
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
            assert violations[0].file_path == Path("/test/changed.py")


class TestRustLinterE2E:
    """End-to-end tests for RustLinterWrapper with realistic scenarios."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            
            # Create source files
            src_dir = project_dir / "src"
            src_dir.mkdir()
            
            # Create test directories
            test_dir = project_dir / "test"
            test_dir.mkdir()
            (test_dir / "unit").mkdir()
            (test_dir / "integration").mkdir()
            (test_dir / "e2e").mkdir()
            
            yield project_dir
    
    @pytest.mark.e2e
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_full_project_lint_workflow(self, mock_rust_module, temp_project):
        """Test complete workflow of linting a project."""
        # Setup
        config = ProboscisConfig(
            test_directories=["test"],
            test_patterns=["test_*.py", "*_test.py"],
            exclude_patterns=["**/build/**"],
            rules={
                "PL001": {"enabled": True},
                "PL002": {"enabled": True},
                "PL003": {"enabled": False}
            }
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Simulate a realistic project with various violations
        project_violations = []
        
        # File 1: Module with missing tests
        for rule in ["PL001:require-unit-test", "PL002:require-integration-test", "PL003:require-e2e-test"]:
            violation = Mock()
            violation.rule_name = rule
            violation.file_path = str(temp_project / "src" / "calculator.py")
            violation.line_number = 10
            violation.function_name = "add"
            violation.message = f"Function 'add' missing {rule.split(':')[1].replace('-', ' ')}"
            violation.severity = "error"
            project_violations.append(violation)
        
        # File 2: Utils module with partial tests
        utils_violation = Mock()
        utils_violation.rule_name = "PL001:require-unit-test"
        utils_violation.file_path = str(temp_project / "src" / "utils.py")
        utils_violation.line_number = 25
        utils_violation.function_name = "format_date"
        utils_violation.message = "Function 'format_date' missing unit test"
        utils_violation.severity = "error"
        project_violations.append(utils_violation)
        
        mock_rust_linter.lint_project.return_value = project_violations
        
        # Execute
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(temp_project)
        
        # Verify
        assert len(violations) == 3  # PL003 is disabled
        
        # Check that violations are properly filtered and converted
        calc_violations = [v for v in violations if "calculator.py" in str(v.file_path)]
        assert len(calc_violations) == 2  # PL001 and PL002 only
        
        utils_violations = [v for v in violations if "utils.py" in str(v.file_path)]
        assert len(utils_violations) == 1
        assert utils_violations[0].function_name == "format_date"
    
    @pytest.mark.e2e
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_git_changed_files_workflow(self, mock_rust_module, temp_project):
        """Test workflow for linting only changed files in a git repository."""
        # Setup
        config = ProboscisConfig()
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Simulate changed files with violations
        changed_violations = []
        
        # Changed file 1: New feature
        for i, (rule, test_type) in enumerate([
            ("PL001:require-unit-test", "unit"),
            ("PL002:require-integration-test", "integration"),
            ("PL003:require-e2e-test", "e2e")
        ]):
            violation = Mock()
            violation.rule_name = rule
            violation.file_path = str(temp_project / "src" / "new_feature.py")
            violation.line_number = 15 + i * 10
            violation.function_name = f"process_{test_type}_data"
            violation.message = f"Function 'process_{test_type}_data' missing {test_type} test"
            violation.severity = "error"
            changed_violations.append(violation)
        
        # Changed file 2: Modified existing file
        violation = Mock()
        violation.rule_name = "PL001:require-unit-test"
        violation.file_path = str(temp_project / "src" / "existing_module.py")
        violation.line_number = 42
        violation.function_name = "updated_function"
        violation.message = "Function 'updated_function' missing unit test"
        violation.severity = "error"
        changed_violations.append(violation)
        
        mock_rust_linter.lint_changed_files.return_value = changed_violations
        
        # Execute
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_changed_files(temp_project)
        
        # Verify
        assert len(violations) == 4
        
        # Check different files
        new_feature_violations = [v for v in violations if "new_feature.py" in str(v.file_path)]
        assert len(new_feature_violations) == 3
        
        existing_violations = [v for v in violations if "existing_module.py" in str(v.file_path)]
        assert len(existing_violations) == 1
        assert existing_violations[0].function_name == "updated_function"
    
    @pytest.mark.e2e
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_large_project_performance_scenario(self, mock_rust_module, temp_project):
        """Test handling of large project with many files and violations."""
        # Setup
        config = ProboscisConfig(
            test_directories=["tests", "test"],
            exclude_patterns=["**/vendor/**", "**/node_modules/**", "**/.venv/**"]
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Simulate a large project with many violations
        large_violations = []
        
        # Generate violations for 100 files
        for file_idx in range(100):
            module_name = f"module_{file_idx}"
            file_path = str(temp_project / "src" / f"{module_name}.py")
            
            # Each file has 2-5 functions with violations
            num_functions = 2 + (file_idx % 4)
            for func_idx in range(num_functions):
                for rule in ["PL001:require-unit-test", "PL002:require-integration-test"]:
                    if (file_idx + func_idx) % 3 != 0:  # Skip some to add variety
                        violation = Mock()
                        violation.rule_name = rule
                        violation.file_path = file_path
                        violation.line_number = 10 + func_idx * 20
                        violation.function_name = f"function_{func_idx}"
                        violation.message = f"Missing test for function_{func_idx}"
                        violation.severity = "error"
                        large_violations.append(violation)
        
        mock_rust_linter.lint_project.return_value = large_violations
        
        # Execute
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(temp_project)
        
        # Verify
        assert len(violations) > 500  # Should have many violations
        
        # Check that all violations are properly converted
        assert all(isinstance(v.file_path, Path) for v in violations)
        assert all(v.severity in ["error", "warning"] for v in violations)
        
        # Verify variety in violations
        unique_files = {str(v.file_path) for v in violations}
        assert len(unique_files) == 100
    
    @pytest.mark.e2e
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_mixed_language_project(self, mock_rust_module, temp_project):
        """Test linting a project with mixed Python and non-Python files."""
        # Setup
        config = ProboscisConfig(
            test_patterns=["test_*.py", "*_test.py", "*_spec.py"],
            exclude_patterns=["*.js", "*.ts", "*.md"]
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Create violations only for Python files
        python_violations = []
        
        # Python files with violations
        for module in ["api", "core", "utils", "models"]:
            violation = Mock()
            violation.rule_name = "PL001:require-unit-test"
            violation.file_path = str(temp_project / "src" / f"{module}.py")
            violation.line_number = 20
            violation.function_name = f"{module}_handler"
            violation.message = f"Function '{module}_handler' missing unit test"
            violation.severity = "error"
            python_violations.append(violation)
        
        mock_rust_linter.lint_project.return_value = python_violations
        
        # Execute
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(temp_project)
        
        # Verify
        assert len(violations) == 4
        assert all(str(v.file_path).endswith(".py") for v in violations)
        
        # Check specific modules
        module_names = {v.function_name.replace("_handler", "") for v in violations}
        assert module_names == {"api", "core", "utils", "models"}
    
    @pytest.mark.e2e
    @patch('proboscis_linter.rust_linter.RUST_AVAILABLE', True)
    @patch('proboscis_linter.rust_linter.proboscis_linter_rust')
    def test_custom_test_structure_project(self, mock_rust_module, temp_project):
        """Test project with custom test directory structure."""
        # Setup custom test structure
        config = ProboscisConfig(
            test_directories=["qa", "quality_assurance", "testing"],
            test_patterns=["check_*.py", "*_check.py", "verify_*.py"]
        )
        
        mock_rust_linter = Mock()
        mock_rust_module.RustLinter.return_value = mock_rust_linter
        
        # Initialize with custom directories
        mock_rust_module.RustLinter.assert_called_with(
            test_directories=["qa", "quality_assurance", "testing"],
            test_patterns=["check_*.py", "*_check.py", "verify_*.py"],
            exclude_patterns=[]
        )
        
        # Create violations for this custom structure
        custom_violations = []
        
        modules = ["authentication", "authorization", "validation"]
        for module in modules:
            for rule_type in ["unit", "integration", "e2e"]:
                violation = Mock()
                violation.rule_name = f"PL00{['unit', 'integration', 'e2e'].index(rule_type) + 1}:require-{rule_type}-test"
                violation.file_path = str(temp_project / "src" / f"{module}.py")
                violation.line_number = 30
                violation.function_name = f"{module}_check"
                violation.message = f"Function '{module}_check' missing {rule_type} test"
                violation.severity = "error"
                custom_violations.append(violation)
        
        mock_rust_linter.lint_project.return_value = custom_violations
        
        # Execute
        wrapper = RustLinterWrapper(config)
        violations = wrapper.lint_project(temp_project)
        
        # Verify all violations are processed
        assert len(violations) == 9  # 3 modules × 3 test types
        
        # Check that all modules are covered
        covered_modules = {v.function_name.replace("_check", "") for v in violations}
        assert covered_modules == {"authentication", "authorization", "validation"}