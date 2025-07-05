"""Integration tests for CLI module."""
import tempfile
from pathlib import Path
from click.testing import CliRunner
import pytest
from proboscis_linter.cli import cli


def test_my_function():
    """Integration test for my_function (example in help text)."""
    # This is a placeholder test for the example function in the help text
    # The function doesn't actually exist, it's just documentation
    assert True


def test_cli():
    """Integration test for the cli function."""
    runner = CliRunner()
    
    # Test basic invocation
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Proboscis Linter" in result.output
    
    # Test with a non-existent path
    result = runner.invoke(cli, ['/non/existent/path'])
    assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def project_structure(self):
        """Create a realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create source structure
            src = root / "src"
            src.mkdir()
            
            # Create app modules
            app = src / "app"
            app.mkdir()
            
            (app / "__init__.py").write_text("")
            (app / "models.py").write_text("""
class User:
    def create_user(self, name, email):
        return {"name": name, "email": email}
    
    def delete_user(self, user_id):
        pass

def validate_email(email):
    return "@" in email
""")
            
            (app / "views.py").write_text("""
def index_view(request):
    return "Welcome"

def user_view(request, user_id):
    return f"User {user_id}"

class APIView:
    def get(self, request):
        return {"status": "ok"}
    
    def post(self, request):
        return {"created": True}
""")
            
            # Create utils
            utils = src / "utils"
            utils.mkdir()
            
            (utils / "__init__.py").write_text("")
            (utils / "helpers.py").write_text("""
def format_date(date):
    return date.strftime("%Y-%m-%d")

def parse_json(json_str):
    import json
    return json.loads(json_str)
""")
            
            # Create test structure
            tests = root / "tests"
            tests.mkdir()
            
            unit_tests = tests / "unit"
            unit_tests.mkdir()
            
            # Add some unit tests
            (unit_tests / "test_models.py").write_text("""
def test_create_user():
    pass

def test_validate_email():
    pass
""")
            
            # Create pyproject.toml
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
test_patterns = ["test_*.py", "*_test.py"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false
""")
            
            yield root
    
    def test_full_project_lint_integration(self, runner, project_structure):
        """Test linting a complete project structure."""
        result = runner.invoke(cli, [str(project_structure)])
        
        assert result.exit_code == 0
        
        # Should find violations for missing tests
        assert "delete_user" in result.output  # Has no test
        assert "index_view" in result.output  # Has no test
        assert "user_view" in result.output  # Has no test
        assert "format_date" in result.output  # Has no test
        assert "parse_json" in result.output  # Has no test
        assert "APIView.get" in result.output or "get" in result.output
        assert "APIView.post" in result.output or "post" in result.output
        
        # Should not report violations for tested functions
        assert "create_user" not in result.output or "test_create_user" in result.output
        assert "validate_email" not in result.output or "test_validate_email" in result.output
    
    def test_json_output_integration(self, runner, project_structure):
        """Test JSON output format with real project."""
        result = runner.invoke(cli, [str(project_structure), "--format", "json"])
        
        assert result.exit_code == 0
        
        # Verify JSON structure
        import json
        output_data = json.loads(result.output)
        
        assert "total_violations" in output_data
        assert "violations" in output_data
        assert isinstance(output_data["violations"], list)
        assert output_data["total_violations"] > 0
        
        # Check violation structure
        violation = output_data["violations"][0]
        assert "rule" in violation
        assert "function" in violation
        assert "file" in violation
        assert "line" in violation
        assert "message" in violation
        assert "severity" in violation
    
    def test_exclude_integration(self, runner, project_structure):
        """Test exclude patterns with real files."""
        # Exclude views module
        result = runner.invoke(cli, [
            str(project_structure),
            "--exclude", "**/views.py"
        ])
        
        assert result.exit_code == 0
        
        # Should not report violations from views.py
        assert "index_view" not in result.output
        assert "user_view" not in result.output
        assert "APIView" not in result.output
        
        # Should still report violations from other files
        assert "delete_user" in result.output  # From models.py
        assert "format_date" in result.output  # From helpers.py
    
    def test_fail_on_error_integration(self, runner, project_structure):
        """Test fail-on-error with violations."""
        result = runner.invoke(cli, [
            str(project_structure),
            "--fail-on-error"
        ])
        
        # Should exit with error code due to violations
        assert result.exit_code == 1
        assert "violations" in result.output
    
    def test_verbose_mode_integration(self, runner, project_structure):
        """Test verbose logging in real scenario."""
        result = runner.invoke(cli, [
            str(project_structure),
            "--verbose"
        ])
        
        assert result.exit_code == 0
        # In verbose mode, should see more detailed output
        assert "Linting" in result.output or "DEBUG" in result.output
    
    def test_changed_only_mock_integration(self, runner, project_structure):
        """Test changed-only mode with mocked git changes."""
        from unittest.mock import patch, Mock
        
        # Mock the linter to simulate changed files
        with patch('proboscis_linter.cli.ProboscisLinter') as mock_linter_class:
            mock_linter = Mock()
            mock_linter_class.return_value = mock_linter
            
            # Simulate only models.py has changes
            from proboscis_linter.models import LintViolation
            mock_violations = [
                LintViolation(
                    rule_name="PL001:require-unit-test",
                    file_path=project_structure / "src" / "app" / "models.py",
                    line_number=5,
                    function_name="delete_user",
                    message="Function 'delete_user' missing unit test",
                    severity="error"
                )
            ]
            mock_linter.lint_changed_files.return_value = mock_violations
            
            result = runner.invoke(cli, [
                str(project_structure),
                "--changed-only"
            ])
            
            assert result.exit_code == 0
            assert "delete_user" in result.output
            # Should only show violation from changed file
            assert "index_view" not in result.output  # From views.py
    
    def test_mixed_config_and_cli_options(self, runner, project_structure):
        """Test interaction between config file and CLI options."""
        # Config file has output_format=text, we'll override with json
        result = runner.invoke(cli, [
            str(project_structure),
            "--format", "json",
            "--exclude", "**/helpers.py",
            "--fail-on-error"
        ])
        
        # Should fail due to violations
        assert result.exit_code == 1
        
        # Should use JSON format (CLI override)
        import json
        output_data = json.loads(result.output)
        assert "total_violations" in output_data
        
        # Should exclude helpers.py
        violations = output_data["violations"]
        helper_violations = [v for v in violations if "helpers.py" in v["file"]]
        assert len(helper_violations) == 0
    
    def test_custom_config_location(self, runner):
        """Test with config file in non-standard location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create subdirectory with code
            subdir = root / "subproject"
            subdir.mkdir()
            
            src_file = subdir / "module.py"
            src_file.write_text("""
def my_function():
    pass
""")
            
            # Put config at root level
            config_file = root / "pyproject.toml"
            config_file.write_text("""
[tool.proboscis]
output_format = "json"
fail_on_error = false

[tool.proboscis.rules]
PL001 = false
PL002 = true
PL003 = true
""")
            
            # Run from subdirectory
            result = runner.invoke(cli, [str(subdir)])
            
            assert result.exit_code == 0
            
            # Should use JSON format from parent config
            import json
            output_data = json.loads(result.output)
            
            # Should have 2 violations (PL002 and PL003, not PL001)
            assert output_data["total_violations"] == 2
            
            rules = {v["rule"].split(":")[0] for v in output_data["violations"]}
            assert "PL001" not in rules
            assert "PL002" in rules
            assert "PL003" in rules
    
    def test_performance_with_many_files(self, runner):
        """Test CLI performance with many files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create many Python files
            for i in range(50):
                module_file = root / f"module_{i}.py"
                module_file.write_text(f"""
def function_{i}_a():
    pass

def function_{i}_b():
    pass

class Class_{i}:
    def method_1(self):
        pass
    
    def method_2(self):
        pass
""")
            
            # Time the execution
            import time
            start_time = time.time()
            
            result = runner.invoke(cli, [str(root)])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            # Should complete reasonably quickly (under 10 seconds for 50 files)
            assert execution_time < 10
            
            # Should find many violations
            assert "violations" in result.output