"""Integration tests for linter module."""
import tempfile
import subprocess
from pathlib import Path
import pytest
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig, RuleConfig
from proboscis_linter.models import LintViolation


@pytest.mark.integration
def test_ProboscisLinter_lint_project():
    """Integration test for ProboscisLinter.lint_project method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create a simple project structure
        src = root / "src"
        src.mkdir()
        
        # Create a Python file with functions
        (src / "example.py").write_text("""
def add(a, b):
    return a + b

def subtract(x, y):
    return x - y
""")
        
        # Create test directory
        test_dir = root / "test"
        test_dir.mkdir()
        
        # Configure and run linter
        config = ProboscisConfig(
            test_directories=["test"],
            test_patterns=["test_*.py"]
        )
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Should find violations for missing tests
        assert len(violations) > 0
        assert any(v.function_name == "add" for v in violations)
        assert any(v.function_name == "subtract" for v in violations)


@pytest.mark.integration
def test_ProboscisLinter_lint_file():
    """Integration test for ProboscisLinter.lint_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create a Python file
        file_path = root / "module.py"
        file_path.write_text("""
def process_data(data):
    return data * 2

def validate_input(value):
    return isinstance(value, int)
""")
        
        # Create test directory
        test_dir = root / "test"
        test_dir.mkdir()
        
        # Run linter on single file
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        violations = linter.lint_file(file_path, [test_dir])
        
        # Should find violations
        assert len(violations) > 0
        assert any(v.function_name == "process_data" for v in violations)
        assert any(v.function_name == "validate_input" for v in violations)


@pytest.mark.integration
def test_ProboscisLinter_lint_changed_files():
    """Integration test for ProboscisLinter.lint_changed_files method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=root, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, capture_output=True)
        
        # Create initial file and commit
        initial_file = root / "initial.py"
        initial_file.write_text("# Initial file")
        subprocess.run(["git", "add", "."], cwd=root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=root, capture_output=True)
        
        # Create changed file
        changed_file = root / "changed.py"
        changed_file.write_text("""
def new_function():
    return "new"

def another_new_function():
    return "another"
""")
        
        # Create test directory
        (root / "test").mkdir()
        
        # Run linter on changed files
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        violations = linter.lint_changed_files(root)
        
        # Should find violations only for the new file
        assert len(violations) > 0
        assert all(str(v.file_path).endswith("changed.py") for v in violations)


class TestLinterIntegration:
    """Integration tests for ProboscisLinter."""
    
    @pytest.fixture
    def complex_project(self):
        """Create a complex project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create source structure
            src = root / "src"
            src.mkdir()
            
            # Main module
            (src / "main.py").write_text("""
def initialize_app():
    pass

def run_server(port=8000):
    pass

class Application:
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def restart(self):
        pass
""")
            
            # Utils module
            utils = src / "utils"
            utils.mkdir()
            (utils / "__init__.py").write_text("")
            (utils / "helpers.py").write_text("""
def validate_input(data):
    return True

def format_output(data):
    return str(data)

def log_message(msg):  # noqa: PL001
    print(msg)
""")
            
            # Database module
            db = src / "database"
            db.mkdir()
            (db / "__init__.py").write_text("")
            (db / "models.py").write_text("""
class User:
    def save(self):
        pass
    
    def delete(self):
        pass
    
    @classmethod
    def find_by_id(cls, id):
        pass

class Session:
    def create(self):
        pass
    
    def validate(self):
        pass
""")
            
            # Create test structure
            tests = root / "test"
            tests.mkdir()
            
            # Unit tests
            unit = tests / "unit"
            unit.mkdir()
            (unit / "test_main.py").write_text("""
@pytest.mark.integration
def test_initialize_app():
    pass

@pytest.mark.integration
def test_Application_start():
    pass
""")
            
            (unit / "test_helpers.py").write_text("""
@pytest.mark.integration
def test_validate_input():
    pass
""")
            
            # Integration tests
            integration = tests / "integration"
            integration.mkdir()
            (integration / "test_database.py").write_text("""
@pytest.mark.integration
def test_User_save():
    pass

@pytest.mark.integration
def test_Session_create():
    pass
""")
            
            # E2E tests
            e2e = tests / "e2e"
            e2e.mkdir()
            (e2e / "test_application.py").write_text("""
@pytest.mark.integration
def test_Application_restart():
    pass
""")
            
            yield root
    
    @pytest.mark.integration
    def test_lint_complex_project(self, complex_project):
        """Test linting a complex project with various scenarios."""
        linter = ProboscisLinter()
        violations = linter.lint_project(complex_project)
        
        # Analyze violations
        violations_by_function = {}
        for v in violations:
            if v.function_name not in violations_by_function:
                violations_by_function[v.function_name] = []
            violations_by_function[v.function_name].append(v)
        
        # Check specific functions
        # initialize_app has unit test
        assert "initialize_app" not in violations_by_function or \
               all("PL001" not in v.rule_name for v in violations_by_function.get("initialize_app", []))
        
        # run_server has no tests
        assert "run_server" in violations_by_function
        assert len(violations_by_function["run_server"]) == 3  # PL001, PL002, PL003
        
        # Application.start has unit test
        assert "Application.start" not in violations_by_function or \
               all("PL001" not in v.rule_name for v in violations_by_function.get("Application.start", []))
        
        # Application.stop has no tests
        assert "Application.stop" in violations_by_function
        
        # log_message has noqa for PL001
        log_violations = violations_by_function.get("log_message", [])
        assert all("PL001" not in v.rule_name for v in log_violations)
        assert len(log_violations) == 2  # Only PL002 and PL003
    
    @pytest.mark.integration
    def test_lint_with_custom_config(self, complex_project):
        """Test linting with custom configuration."""
        # Custom config with different test patterns
        config = ProboscisConfig(
            test_directories=["test", "spec"],
            test_patterns=["test_*.py", "*_test.py", "*_spec.py"],
            exclude_patterns=["**/database/**"],  # Exclude database module
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),  # Disable integration test requirement
                "PL003": RuleConfig(enabled=True)
            }
        )
        
        linter = ProboscisLinter(config)
        violations = linter.lint_project(complex_project)
        
        # Should not have any violations from database module
        assert all("database" not in str(v.file_path) for v in violations)
        
        # Should not have any PL002 violations
        assert all("PL002" not in v.rule_name for v in violations)
        
        # Should still have PL001 and PL003 violations
        rule_types = {v.rule_name.split(":")[0] for v in violations}
        assert "PL001" in rule_types
        assert "PL003" in rule_types
        assert "PL002" not in rule_types
    
    @pytest.mark.integration
    def test_lint_changed_files_integration(self, complex_project):
        """Test linting changed files with mocked git changes."""
        from unittest.mock import patch, Mock
        
        # Mock the rust linter to simulate changed files
        with patch('proboscis_linter.linter.RustLinterWrapper') as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper
            
            # Simulate that only main.py and helpers.py have changes
            mock_violations = [
                LintViolation(
                    rule_name="PL001:require-unit-test",
                    file_path=complex_project / "src" / "main.py",
                    line_number=4,
                    function_name="run_server",
                    message="Function 'run_server' missing unit test",
                    severity="error"
                ),
                LintViolation(
                    rule_name="PL002:require-integration-test",
                    file_path=complex_project / "src" / "utils" / "helpers.py",
                    line_number=5,
                    function_name="format_output",
                    message="Function 'format_output' missing integration test",
                    severity="error"
                )
            ]
            mock_wrapper.lint_changed_files.return_value = mock_violations
            
            linter = ProboscisLinter()
            violations = linter.lint_changed_files(complex_project)
            
            assert len(violations) == 2
            assert violations[0].function_name == "run_server"
            assert violations[1].function_name == "format_output"
    
    @pytest.mark.integration
    def test_incremental_test_development(self, complex_project):
        """Test how violations change as tests are added incrementally."""
        linter = ProboscisLinter()
        
        # Initial state - get baseline violations
        initial_violations = linter.lint_project(complex_project)
        initial_count = len(initial_violations)
        
        # Add more unit tests
        unit_test_file = complex_project / "test" / "unit" / "test_main.py"
        unit_test_file.write_text(unit_test_file.read_text() + """
@pytest.mark.integration
def test_run_server():
    pass

@pytest.mark.integration
def test_Application_stop():
    pass
""")
        
        # Check violations after adding unit tests
        after_unit_violations = linter.lint_project(complex_project)
        after_unit_count = len(after_unit_violations)
        
        # Should have fewer violations
        assert after_unit_count < initial_count
        
        # run_server should no longer have PL001 violation
        run_server_violations = [v for v in after_unit_violations 
                                if v.function_name == "run_server"]
        assert all("PL001" not in v.rule_name for v in run_server_violations)
        
        # Add integration tests
        integration_test_file = complex_project / "test" / "integration" / "test_main_integration.py"
        integration_test_file.write_text("""
@pytest.mark.integration
def test_run_server_integration():
    pass

@pytest.mark.integration
def test_Application_stop_integration():
    pass
""")
        
        # Check violations after adding integration tests
        final_violations = linter.lint_project(complex_project)
        final_count = len(final_violations)
        
        # Should have even fewer violations
        assert final_count < after_unit_count
    
    @pytest.mark.integration
    def test_mixed_test_locations(self):
        """Test handling of tests in non-standard locations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create source files
            src = root / "src"
            src.mkdir()
            (src / "module.py").write_text("""
def func1():
    pass

def func2():
    pass

def func3():
    pass
""")
            
            # Tests in different locations
            # Standard location
            standard_tests = root / "test" / "unit"
            standard_tests.mkdir(parents=True)
            (standard_tests / "test_module.py").write_text("""
@pytest.mark.integration
def test_func1():
    pass
""")
            
            # Alternative location
            alt_tests = root / "tests"
            alt_tests.mkdir()
            (alt_tests / "test_module.py").write_text("""
@pytest.mark.integration
def test_func2():
    pass
""")
            
            # Custom location (not in default config)
            custom_tests = root / "spec"
            custom_tests.mkdir()
            (custom_tests / "module_spec.py").write_text("""
@pytest.mark.integration
def test_func3():
    pass
""")
            
            # Test with default config
            linter = ProboscisLinter()
            violations = linter.lint_project(root)
            
            # func1 and func2 should have their tests found in standard locations
            func_violations = {v.function_name for v in violations if "PL001" in v.rule_name}
            
            # func3 should have violations (test in non-standard location)
            assert "func3" in func_violations
            
            # Test with custom config including "spec"
            config = ProboscisConfig(
                test_directories=["test", "tests", "spec"],
                test_patterns=["test_*.py", "*_test.py", "*_spec.py"]
            )
            linter_custom = ProboscisLinter(config)
            violations_custom = linter_custom.lint_project(root)
            
            # Now func3 should also have its test found
            func_violations_custom = {v.function_name for v in violations_custom if "PL001" in v.rule_name}
            assert "func3" not in func_violations_custom or len(func_violations_custom) == 0
    
    @pytest.mark.integration
    def test_performance_with_many_files(self):
        """Test linter performance with many files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create many modules
            for i in range(20):
                module_dir = root / f"module_{i}"
                module_dir.mkdir()
                
                for j in range(5):
                    module_file = module_dir / f"file_{j}.py"
                    module_file.write_text(f"""
def function_{i}_{j}_a():
    pass

def function_{i}_{j}_b():
    pass

class Class_{i}_{j}:
    def method1(self):
        pass
    
    def method2(self):
        pass
""")
            
            # Add some tests
            test_dir = root / "test" / "unit"
            test_dir.mkdir(parents=True)
            
            for i in range(5):  # Only test first 5 modules
                test_file = test_dir / f"test_module_{i}.py"
                test_file.write_text(f"""
def test_function_{i}_0_a():
    pass

def test_Class_{i}_0_method1():
    pass
""")
            
            # Time the linting
            import time
            start_time = time.time()
            
            linter = ProboscisLinter()
            violations = linter.lint_project(root)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete in reasonable time
            assert execution_time < 30  # 30 seconds for 100 files
            
            # Should find many violations
            assert len(violations) > 100
            
            # Verify some functions have tests and others don't
            tested_functions = {"function_0_0_a", "function_1_0_a", "function_2_0_a", 
                               "function_3_0_a", "function_4_0_a"}
            
            untested_violations = [v for v in violations 
                                  if v.function_name not in tested_functions 
                                  and "PL001" in v.rule_name]
            assert len(untested_violations) > 50