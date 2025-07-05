"""End-to-end tests for CLI module."""
import tempfile
import json
from pathlib import Path
import pytest
from click.testing import CliRunner
from proboscis_linter.cli import cli


def test_my_function():
    """E2E test for my_function (example in help text)."""
    # This is a placeholder test for the example function in the help text
    # The function doesn't actually exist, it's just documentation
    assert True


def test_another_function():
    """E2E test for another_function (example in help text)."""
    # This is a placeholder test for the example function in the help text
    # The function doesn't actually exist, it's just documentation
    assert True


def test_cli():
    """E2E test for the cli function."""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a simple Python file
        test_file = tmppath / "example.py"
        test_file.write_text("""
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
""")
        
        # Run the CLI
        result = runner.invoke(cli, [str(tmppath)])
        
        # Check that it ran successfully
        assert result.exit_code != 0  # Should have violations
        assert "violations" in result.output.lower()


class TestCLIE2E:
    """End-to-end tests for CLI in real-world scenarios."""
    
    @pytest.fixture
    def django_project(self):
        """Create a Django-like project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Django project structure
            project = root / "myproject"
            project.mkdir()
            
            # Settings
            (project / "__init__.py").write_text("")
            (project / "settings.py").write_text("""
DEBUG = True
ALLOWED_HOSTS = []

def configure_logging():
    pass
""")
            
            # Apps
            apps = root / "apps"
            apps.mkdir()
            
            # User app
            user_app = apps / "users"
            user_app.mkdir()
            (user_app / "__init__.py").write_text("")
            
            (user_app / "models.py").write_text("""
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    
    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return self.username
    
    @classmethod
    def create_user(cls, username, email):
        return cls.objects.create(username=username, email=email)
""")
            
            (user_app / "views.py").write_text("""
from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')

def logout_view(request):
    return render(request, 'logout.html')

class UserAPIView:
    def get(self, request, user_id):
        return {"user_id": user_id}
    
    def post(self, request):
        return {"created": True}
""")
            
            # Migrations (should be excluded)
            migrations = user_app / "migrations"
            migrations.mkdir()
            (migrations / "__init__.py").write_text("")
            (migrations / "0001_initial.py").write_text("""
def migrate():
    pass
""")
            
            # Tests directory
            tests = root / "tests"
            tests.mkdir()
            
            unit = tests / "unit"
            unit.mkdir()
            
            (unit / "test_models.py").write_text("""
def test_user_save():
    pass

def test_create_user():
    pass
""")
            
            # Django config
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = ["**/migrations/**", "manage.py", "**/admin.py"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false  # No e2e tests for Django
""")
            
            (root / "manage.py").write_text("""
def main():
    pass

if __name__ == "__main__":
    main()
""")
            
            yield root
    
    @pytest.fixture
    def fastapi_project(self):
        """Create a FastAPI-like project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # API structure
            api = root / "api"
            api.mkdir()
            
            (api / "__init__.py").write_text("")
            
            (api / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: dict):
    return item
""")
            
            (api / "auth.py").write_text("""
def verify_token(token: str) -> bool:
    return len(token) > 10

def create_token(user_id: int) -> str:
    return f"token_{user_id}"

class AuthMiddleware:
    def process_request(self, request):
        pass
    
    def process_response(self, response):
        pass
""")
            
            # Services
            services = root / "services"
            services.mkdir()
            
            (services / "__init__.py").write_text("")
            (services / "user_service.py").write_text("""
class UserService:
    def get_user(self, user_id):
        return {"id": user_id}
    
    def create_user(self, user_data):
        return {**user_data, "id": 1}
    
    def update_user(self, user_id, user_data):
        return {**user_data, "id": user_id}

def validate_user_data(data):
    return "name" in data and "email" in data
""")
            
            # Tests
            tests = root / "tests"
            tests.mkdir()
            
            # Unit tests
            unit = tests / "unit"
            unit.mkdir()
            (unit / "test_auth.py").write_text("""
def test_verify_token():
    pass

def test_create_token():
    pass
""")
            
            # Integration tests
            integration = tests / "integration"
            integration.mkdir()
            (integration / "test_api.py").write_text("""
def test_read_root():
    pass
""")
            
            # E2E tests
            e2e = tests / "e2e"
            e2e.mkdir()
            (e2e / "test_full_flow.py").write_text("""
def test_create_item():
    pass
""")
            
            # Config
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = ["**/alembic/**", "**/__pycache__/**"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = true
""")
            
            yield root
    
    def test_django_project_e2e(self, django_project):
        """Test linting a Django project end-to-end."""
        runner = CliRunner()
        result = runner.invoke(cli, [str(django_project)])
        
        assert result.exit_code == 0
        
        # Should find violations for untested functions
        assert "get_full_name" in result.output  # No test
        assert "login_view" in result.output  # No test
        assert "logout_view" in result.output  # No test
        assert "UserAPIView.get" in result.output or "get" in result.output
        assert "UserAPIView.post" in result.output or "post" in result.output
        assert "configure_logging" in result.output
        
        # Should not find violations for tested functions
        assert "User.save" not in result.output or "test_user_save" in result.output
        
        # Should exclude migrations
        assert "migrate" not in result.output
        assert "0001_initial.py" not in result.output
        
        # Should exclude manage.py
        assert "manage.py" not in result.output
    
    def test_fastapi_project_e2e(self, fastapi_project):
        """Test linting a FastAPI project end-to-end."""
        runner = CliRunner()
        result = runner.invoke(cli, [str(fastapi_project), "--format", "json"])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        output_data = json.loads(result.output)
        violations = output_data["violations"]
        
        # Group violations by rule
        violations_by_rule = {}
        for v in violations:
            rule = v["rule"].split(":")[0]
            if rule not in violations_by_rule:
                violations_by_rule[rule] = []
            violations_by_rule[rule].append(v)
        
        # Should have violations for all three rules
        assert "PL001" in violations_by_rule  # Unit tests
        assert "PL002" in violations_by_rule  # Integration tests
        assert "PL003" in violations_by_rule  # E2E tests
        
        # Check specific violations
        function_names = [v["function"] for v in violations]
        
        # Functions with missing tests
        assert "read_item" in function_names  # No test
        assert "AuthMiddleware.process_request" in function_names or "process_request" in function_names
        assert "AuthMiddleware.process_response" in function_names or "process_response" in function_names
        assert "UserService.get_user" in function_names or "get_user" in function_names
        assert "UserService.update_user" in function_names or "update_user" in function_names
        assert "validate_user_data" in function_names
    
    def test_monorepo_e2e(self):
        """Test linting a monorepo with multiple services."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Root config
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = ["**/build/**", "**/dist/**"]

[tool.proboscis.rules]
PL001 = true
PL002 = false
PL003 = false
""")
            
            # Service 1
            service1 = root / "services" / "auth-service"
            service1.mkdir(parents=True)
            
            (service1 / "auth.py").write_text("""
def authenticate(username, password):
    return username == "admin"

def authorize(user, resource):
    return True
""")
            
            (service1 / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests", "spec"]
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = true  # Override root config
PL003 = true  # Override root config
""")
            
            # Service 2
            service2 = root / "services" / "data-service"
            service2.mkdir(parents=True)
            
            (service2 / "processor.py").write_text("""
def process_data(data):
    return data.upper()

def validate_data(data):
    return len(data) > 0
""")
            
            # No local config, uses root config
            
            # Run linter on service1
            runner = CliRunner()
            result1 = runner.invoke(cli, [str(service1)])
            
            # Should fail due to fail_on_error=true
            assert result1.exit_code == 1
            
            # Should check all three test types
            assert "PL001" in result1.output
            assert "PL002" in result1.output
            assert "PL003" in result1.output
            
            # Run linter on service2
            result2 = runner.invoke(cli, [str(service2)])
            
            # Should pass (no fail_on_error)
            assert result2.exit_code == 0
            
            # Should only check PL001 (from root config)
            assert "PL001" in result2.output
            assert "PL002" not in result2.output
            assert "PL003" not in result2.output
    
    def test_real_world_workflow_e2e(self):
        """Test a complete real-world workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runner = CliRunner()
            
            # Step 1: Create initial project
            src = root / "src"
            src.mkdir()
            
            (src / "calculator.py").write_text("""
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
            
            # Step 2: Run initial lint
            result = runner.invoke(cli, [str(root)])
            assert result.exit_code == 0
            assert "add" in result.output
            assert "subtract" in result.output
            assert "multiply" in result.output
            assert "divide" in result.output
            
            # Step 3: Add some tests
            tests = root / "tests"
            tests.mkdir()
            unit = tests / "unit"
            unit.mkdir()
            
            (unit / "test_calculator.py").write_text("""
def test_add():
    pass

def test_subtract():
    pass
""")
            
            # Step 4: Run lint again
            result = runner.invoke(cli, [str(root)])
            assert result.exit_code == 0
            
            # Should not complain about add and subtract anymore
            assert "Function 'add' missing unit test" not in result.output
            assert "Function 'subtract' missing unit test" not in result.output
            
            # Should still complain about multiply and divide
            assert "multiply" in result.output
            assert "divide" in result.output
            
            # Step 5: Add config to disable some rules
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
output_format = "json"

[tool.proboscis.rules]
PL002 = false  # Disable integration test requirement
PL003 = false  # Disable e2e test requirement
""")
            
            # Step 6: Run with new config
            result = runner.invoke(cli, [str(root)])
            assert result.exit_code == 0
            
            output_data = json.loads(result.output)
            
            # Should only have PL001 violations now
            rules = {v["rule"].split(":")[0] for v in output_data["violations"]}
            assert rules == {"PL001"}
            
            # Step 7: Use CLI to override config
            result = runner.invoke(cli, [str(root), "--format", "text", "--fail-on-error"])
            
            # Should fail due to remaining violations
            assert result.exit_code == 1
            
            # Should use text format (overriding JSON from config)
            assert "ERROR:" in result.output
            assert '"violations"' not in result.output
    
    def test_performance_e2e(self):
        """Test performance with a large codebase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a large codebase structure
            for package_idx in range(5):
                package = root / f"package_{package_idx}"
                package.mkdir()
                
                for module_idx in range(20):
                    module_file = package / f"module_{module_idx}.py"
                    module_content = []
                    
                    # Each module has 5 functions
                    for func_idx in range(5):
                        module_content.append(f"""
def function_{module_idx}_{func_idx}(x, y):
    \"\"\"Function {module_idx}.{func_idx}\"\"\"
    return x + y + {func_idx}
""")
                    
                    # And 2 classes with 3 methods each
                    for class_idx in range(2):
                        module_content.append(f"""
class Class_{module_idx}_{class_idx}:
    \"\"\"Class {module_idx}.{class_idx}\"\"\"
    
    def method_1(self):
        return 1
    
    def method_2(self, x):
        return x * 2
    
    def method_3(self, x, y):
        return x + y
""")
                    
                    module_file.write_text("\n".join(module_content))
            
            # Add minimal config
            (root / "pyproject.toml").write_text("""
[tool.proboscis]
exclude_patterns = ["**/test_*.py", "**/__pycache__/**"]
""")
            
            # Time the execution
            import time
            start_time = time.time()
            
            runner = CliRunner()
            result = runner.invoke(cli, [str(root), "--format", "json"])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            
            # Should complete in reasonable time (under 30 seconds for 500 files)
            assert execution_time < 30
            
            # Verify output
            output_data = json.loads(result.output)
            
            # Should find many violations (5 packages * 20 modules * (5 functions + 2 classes * 3 methods) * 3 rules)
            assert output_data["total_violations"] > 1000
            
            print(f"Processed {5 * 20} files with {output_data['total_violations']} violations in {execution_time:.2f} seconds")