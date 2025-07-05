"""End-to-end tests for report generator module."""
import tempfile
import json
from pathlib import Path
import pytest
from click.testing import CliRunner
from proboscis_linter.cli import cli
from proboscis_linter.models import LintViolation
from proboscis_linter.report_generator import TextReportGenerator, JsonReportGenerator


@pytest.mark.e2e
def test_TextReportGenerator_generate_report():
    """E2E test for TextReportGenerator.generate_report method."""
    generator = TextReportGenerator()
    
    # Create realistic violations
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("/project/src/auth/login.py"),
            line_number=15,
            function_name="authenticate_user",
            message="Function 'authenticate_user' missing unit test",
            severity="error"
        ),
        LintViolation(
            rule_name="PL002:require-integration-test",
            file_path=Path("/project/src/api/endpoints.py"),
            line_number=42,
            function_name="get_user_data",
            message="Function 'get_user_data' missing integration test",
            severity="error"
        )
    ]
    
    report = generator.generate_report(violations)
    
    # Verify report content
    assert "Found 2 violations:" in report
    assert "authenticate_user" in report
    assert "get_user_data" in report
    assert "PL001" in report
    assert "PL002" in report


@pytest.mark.e2e
def test_TextReportGenerator_get_format_name():
    """E2E test for TextReportGenerator.get_format_name method."""
    generator = TextReportGenerator()
    name = generator.get_format_name()
    assert name == "text"
    assert isinstance(name, str)


@pytest.mark.e2e
def test_JsonReportGenerator_generate_report():
    """E2E test for JsonReportGenerator.generate_report method."""
    generator = JsonReportGenerator()
    
    # Create realistic violations
    violations = [
        LintViolation(
            rule_name="PL003:require-e2e-test",
            file_path=Path("/project/src/workflow/pipeline.py"),
            line_number=100,
            function_name="process_data",
            message="Function 'process_data' missing e2e test",
            severity="error"
        )
    ]
    
    report = generator.generate_report(violations)
    
    # Verify JSON structure
    data = json.loads(report)
    assert data["total_violations"] == 1
    assert data["summary"]["error"] == 1
    assert data["summary"]["warning"] == 0
    assert len(data["violations"]) == 1
    
    violation = data["violations"][0]
    assert violation["function_name"] == "process_data"
    assert violation["line_number"] == 100


@pytest.mark.e2e
def test_JsonReportGenerator_get_format_name():
    """E2E test for JsonReportGenerator.get_format_name method."""
    generator = JsonReportGenerator()
    name = generator.get_format_name()
    assert name == "json"
    assert isinstance(name, str)


class TestReportGeneratorE2E:
    """End-to-end tests for report generators in real-world scenarios."""
    
    @pytest.fixture
    def real_project(self):
        """Create a realistic project for testing report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a multi-package project
            packages = ["auth", "api", "database", "utils"]
            
            for package in packages:
                pkg_dir = root / "src" / package
                pkg_dir.mkdir(parents=True)
                (pkg_dir / "__init__.py").write_text("")
                
                # Add various modules to each package
                if package == "auth":
                    (pkg_dir / "authentication.py").write_text("""
def login(username, password):
    return {"token": "abc123"}

def logout(token):
    return {"success": True}

def verify_token(token):
    return token == "abc123"

class AuthManager:
    def create_user(self, username, password):
        return {"id": 1, "username": username}
    
    def delete_user(self, user_id):
        return {"deleted": user_id}
    
    def update_password(self, user_id, new_password):
        return {"updated": True}
""")
                
                elif package == "api":
                    (pkg_dir / "endpoints.py").write_text("""
def get_users(page=1, limit=10):
    return {"users": [], "page": page}

def get_user_by_id(user_id):
    return {"id": user_id, "name": "Test User"}

def create_user(user_data):
    return {"id": 1, **user_data}

def update_user(user_id, user_data):
    return {"id": user_id, **user_data}

def delete_user(user_id):
    return {"deleted": True}
""")
                
                elif package == "database":
                    (pkg_dir / "models.py").write_text("""
class User:
    def save(self):
        pass
    
    def delete(self):
        pass
    
    @classmethod
    def find_by_id(cls, user_id):
        pass
    
    @classmethod
    def find_by_username(cls, username):
        pass

class Session:
    def create(self, user_id):
        pass
    
    def validate(self):
        pass
    
    def expire(self):
        pass
""")
                
                elif package == "utils":
                    (pkg_dir / "helpers.py").write_text("""
def format_date(date):
    return date.strftime("%Y-%m-%d")

def parse_json(json_string):
    import json
    return json.loads(json_string)

def generate_uuid():
    import uuid
    return str(uuid.uuid4())

def hash_password(password):
    return f"hashed_{password}"

def validate_email(email):
    return "@" in email and "." in email
""")
            
            # Add some tests (incomplete coverage)
            test_dir = root / "tests" / "unit"
            test_dir.mkdir(parents=True)
            
            (test_dir / "test_auth.py").write_text("""
@pytest.mark.e2e
def test_login():
    pass

@pytest.mark.e2e
def test_verify_token():
    pass
""")
            
            (test_dir / "test_utils.py").write_text("""
@pytest.mark.e2e
def test_validate_email():
    pass

@pytest.mark.e2e
def test_format_date():
    pass
""")
            
            # Add configuration
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = ["**/migrations/**", "**/__pycache__/**"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false  # Disable e2e requirement
""")
            
            yield root
    
    @pytest.mark.e2e
    def test_text_report_real_project(self, real_project):
        """Test text report generation with a real project."""
        runner = CliRunner()
        result = runner.invoke(cli, [str(real_project)])
        
        assert result.exit_code == 0
        
        # Check report structure
        assert "Found" in result.output
        assert "violations:" in result.output
        
        # Check various functions are reported
        assert "logout" in result.output  # Missing tests
        assert "AuthManager.create_user" in result.output or "create_user" in result.output
        assert "get_users" in result.output
        assert "User.save" in result.output or "save" in result.output
        assert "generate_uuid" in result.output
        
        # Check file paths are shown
        assert "authentication.py" in result.output
        assert "endpoints.py" in result.output
        assert "models.py" in result.output
        assert "helpers.py" in result.output
        
        # Check line numbers are shown
        assert ":" in result.output  # Line number separator
        
        # Check severity indicators
        assert "ERROR:" in result.output
        
        # Check footer sections
        assert "Total violations:" in result.output
        assert "Tip:" in result.output
        assert "#noqa" in result.output
    
    @pytest.mark.e2e
    def test_json_report_real_project(self, real_project):
        """Test JSON report generation with a real project."""
        runner = CliRunner()
        result = runner.invoke(cli, [str(real_project), "--format", "json"])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        data = json.loads(result.output)
        
        # Check structure
        assert "total_violations" in data
        assert "violations" in data
        assert isinstance(data["violations"], list)
        assert data["total_violations"] > 0
        assert data["total_violations"] == len(data["violations"])
        
        # Check violation details
        for violation in data["violations"]:
            assert "rule" in violation
            assert "function" in violation
            assert "file" in violation
            assert "line" in violation
            assert "message" in violation
            assert "severity" in violation
            
            # Check rule format
            assert violation["rule"].startswith("PL")
            assert ":" in violation["rule"]
            
            # Check file paths are absolute or relative
            assert violation["file"].endswith(".py")
            
            # Check line numbers are positive
            assert violation["line"] > 0
            
            # Check severity is valid
            assert violation["severity"] in ["error", "warning"]
        
        # Check specific content
        functions = {v["function"] for v in data["violations"]}
        files = {v["file"] for v in data["violations"]}
        
        # Should have violations from multiple files
        assert len(files) >= 4
        
        # Should have many different functions
        assert len(functions) >= 10
    
    @pytest.mark.e2e
    def test_report_format_switching(self, real_project):
        """Test switching between report formats."""
        runner = CliRunner()
        
        # Get text report
        text_result = runner.invoke(cli, [str(real_project), "--format", "text"])
        assert text_result.exit_code == 0
        
        # Get JSON report
        json_result = runner.invoke(cli, [str(real_project), "--format", "json"])
        assert json_result.exit_code == 0
        
        # Parse JSON to compare
        json_data = json.loads(json_result.output)
        
        # Both should report same number of violations
        violations_count = json_data["total_violations"]
        assert f"Found {violations_count} violations" in text_result.output
        assert f"Total violations: {violations_count}" in text_result.output
        
        # Extract functions from both reports
        json_functions = {v["function"] for v in json_data["violations"]}
        
        # All JSON functions should appear in text report
        for func in json_functions:
            assert func in text_result.output
    
    @pytest.mark.e2e
    def test_large_report_performance(self):
        """Test report generation performance with many violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create many modules with many functions
            for i in range(50):
                module = root / f"module_{i}.py"
                content = []
                
                for j in range(20):
                    content.append(f"""
def function_{i}_{j}(x, y):
    return x + y

class Class_{i}_{j}:
    def method_a(self):
        pass
    
    def method_b(self, x):
        pass
""")
                
                module.write_text("\n".join(content))
            
            # Run linter and measure time
            import time
            runner = CliRunner()
            
            # Text report
            start = time.time()
            text_result = runner.invoke(cli, [str(root), "--format", "text"])
            text_time = time.time() - start
            
            assert text_result.exit_code == 0
            assert text_time < 60  # Should complete within 60 seconds
            
            # JSON report
            start = time.time()
            json_result = runner.invoke(cli, [str(root), "--format", "json"])
            json_time = time.time() - start
            
            assert json_result.exit_code == 0
            assert json_time < 60  # Should complete within 60 seconds
            
            # Verify output
            json_data = json.loads(json_result.output)
            assert json_data["total_violations"] > 3000  # Many violations
    
    @pytest.mark.e2e
    def test_report_with_config_variations(self, real_project):
        """Test report generation with different configurations."""
        runner = CliRunner()
        
        # Default config (PL001 and PL002 enabled, PL003 disabled)
        result1 = runner.invoke(cli, [str(real_project), "--format", "json"])
        data1 = json.loads(result1.output)
        
        rules1 = {v["rule"].split(":")[0] for v in data1["violations"]}
        assert "PL001" in rules1
        assert "PL002" in rules1
        assert "PL003" not in rules1
        
        # Modify config to enable all rules
        config_file = real_project / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
test_directories = ["tests"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = true  # Now enabled
""")
        
        result2 = runner.invoke(cli, [str(real_project), "--format", "json"])
        data2 = json.loads(result2.output)
        
        # Should have more violations now
        assert data2["total_violations"] > data1["total_violations"]
        
        rules2 = {v["rule"].split(":")[0] for v in data2["violations"]}
        assert "PL001" in rules2
        assert "PL002" in rules2
        assert "PL003" in rules2
    
    @pytest.mark.e2e
    def test_report_cli_integration(self, real_project):
        """Test report generation through full CLI workflow."""
        runner = CliRunner()
        
        # Test 1: Text report with fail-on-error
        result = runner.invoke(cli, [
            str(real_project),
            "--format", "text",
            "--fail-on-error"
        ])
        
        assert result.exit_code == 1  # Should fail due to violations
        assert "ERROR:" in result.output
        assert "Total violations:" in result.output
        
        # Test 2: JSON report with exclusions
        result = runner.invoke(cli, [
            str(real_project),
            "--format", "json",
            "--exclude", "**/database/**"
        ])
        
        assert result.exit_code == 0
        
        data = json.loads(result.output)
        # Should not have violations from database package
        database_violations = [v for v in data["violations"] if "database" in v["file"]]
        assert len(database_violations) == 0
        
        # Test 3: Verbose mode affects report context
        result = runner.invoke(cli, [
            str(real_project),
            "--format", "text",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        # Report should still be generated correctly
        assert "violations" in result.output
        assert "Total violations:" in result.output
    
    @pytest.mark.e2e
    def test_report_special_cases(self):
        """Test report generation with special cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create files with special cases
            special = root / "special_cases.py"
            special.write_text("""
# Unicode function names
def 计算_总和(x, y):
    return x + y

# Very long function name
def this_is_a_very_long_function_name_that_exceeds_normal_length_limits_and_tests_report_formatting():
    pass

# Special characters in name
def func$with$dollars():
    pass

def func_with_underscores_and_numbers_123():
    pass

# Nested functions
def outer_function():
    def inner_function():
        pass
    return inner_function
""")
            
            runner = CliRunner()
            
            # Test text report
            text_result = runner.invoke(cli, [str(root), "--format", "text"])
            assert text_result.exit_code == 0
            
            # Check special cases are handled
            assert "计算_总和" in text_result.output
            assert "this_is_a_very_long_function_name" in text_result.output
            assert "func$with$dollars" in text_result.output
            
            # Test JSON report
            json_result = runner.invoke(cli, [str(root), "--format", "json"])
            assert json_result.exit_code == 0
            
            data = json.loads(json_result.output)
            functions = {v["function"] for v in data["violations"]}
            
            assert "计算_总和" in functions
            assert any("very_long_function_name" in f for f in functions)
            assert "func$with$dollars" in functions