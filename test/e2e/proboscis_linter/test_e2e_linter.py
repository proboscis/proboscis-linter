"""End-to-end tests for linter module."""
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


@pytest.mark.e2e
def test_ProboscisLinter_lint_project():
    """E2E test for ProboscisLinter.lint_project method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create a realistic project
        src = root / "src"
        src.mkdir()
        
        (src / "calculator.py").write_text("""
def add(a, b):
    '''Add two numbers.'''
    return a + b

def multiply(x, y):
    '''Multiply two numbers.'''
    return x * y

class Calculator:
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
""")
        
        # Create empty test directory
        (root / "test").mkdir()
        
        # Run linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Verify violations
        assert len(violations) > 0
        func_names = {v.function_name for v in violations}
        assert "add" in func_names
        assert "multiply" in func_names
        assert "divide" in func_names


@pytest.mark.e2e
def test_ProboscisLinter_lint_file():
    """E2E test for ProboscisLinter.lint_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create project structure
        src = root / "src"
        src.mkdir()
        
        # Create a complex Python file
        complex_file = src / "service.py"
        complex_file.write_text("""
import logging

class UserService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_user(self, username, email):
        '''Create a new user.'''
        self.logger.info(f"Creating user: {username}")
        return {"username": username, "email": email}
    
    def delete_user(self, user_id):
        '''Delete a user by ID.'''
        self.logger.info(f"Deleting user: {user_id}")
        return True

def validate_email(email):
    '''Validate email format.'''
    return "@" in email and "." in email.split("@")[1]

def hash_password(password):
    '''Hash a password.'''
    return f"hashed_{password}"
""")
        
        # Create test directories
        test_dirs = [root / "test", root / "tests"]
        for test_dir in test_dirs:
            test_dir.mkdir()
        
        # Run linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        violations = linter.lint_file(complex_file, test_dirs)
        
        # Verify violations
        assert len(violations) > 0
        func_names = {v.function_name for v in violations}
        assert "create_user" in func_names
        assert "delete_user" in func_names
        assert "validate_email" in func_names
        assert "hash_password" in func_names


@pytest.mark.e2e
def test_ProboscisLinter_lint_changed_files():
    """E2E test for ProboscisLinter.lint_changed_files method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)
        
        # Create and commit initial files
        src = root / "src"
        src.mkdir()
        
        existing_file = src / "existing.py"
        existing_file.write_text("""
def existing_function():
    return "existing"
""")
        
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=root, check=True, capture_output=True)
        
        # Create new and modified files
        new_file = src / "new_feature.py"
        new_file.write_text("""
def feature_one():
    return "one"

def feature_two():
    return "two"

class FeatureManager:
    def process(self):
        return "processed"
""")
        
        # Modify existing file
        existing_file.write_text("""
def existing_function():
    return "existing"

def newly_added_function():
    return "new in existing file"
""")
        
        # Create test directory
        (root / "test").mkdir()
        
        # Run linter on changed files
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        violations = linter.lint_changed_files(root)
        
        # Should find violations for new and modified files
        assert len(violations) > 0
        
        # Check that violations are only from changed files
        file_paths = {str(v.file_path) for v in violations}
        assert any("new_feature.py" in path for path in file_paths)
        assert any("existing.py" in path for path in file_paths)
        
        # Check specific functions
        func_names = {v.function_name for v in violations}
        assert "feature_one" in func_names
        assert "newly_added_function" in func_names


class TestLinterE2E:
    """End-to-end tests for ProboscisLinter in real-world scenarios."""
    
    @pytest.fixture
    def real_python_project(self):
        """Create a realistic Python project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create project structure similar to a real Python package
            # Package structure
            package = root / "mypackage"
            package.mkdir()
            (package / "__init__.py").write_text('"""My Package."""\n__version__ = "0.1.0"')
            
            # Core modules
            core = package / "core"
            core.mkdir()
            (core / "__init__.py").write_text("")
            
            (core / "engine.py").write_text("""
\"\"\"Core engine module.\"\"\"
import logging

logger = logging.getLogger(__name__)


class Engine:
    \"\"\"Main engine class.\"\"\"
    
    def __init__(self, config=None):
        self.config = config or {}
        self._running = False
    
    def start(self):
        \"\"\"Start the engine.\"\"\"
        if self._running:
            raise RuntimeError("Engine already running")
        self._running = True
        logger.info("Engine started")
    
    def stop(self):
        \"\"\"Stop the engine.\"\"\"
        if not self._running:
            raise RuntimeError("Engine not running")
        self._running = False
        logger.info("Engine stopped")
    
    def process(self, data):
        \"\"\"Process data.\"\"\"
        if not self._running:
            raise RuntimeError("Engine not running")
        return self._transform(data)
    
    def _transform(self, data):
        \"\"\"Internal transformation method.\"\"\"
        return data.upper() if isinstance(data, str) else str(data)


def create_engine(config):
    \"\"\"Factory function to create an engine.\"\"\"
    return Engine(config)
""")
            
            # API module
            api = package / "api"
            api.mkdir()
            (api / "__init__.py").write_text("")
            
            (api / "routes.py").write_text("""
\"\"\"API routes module.\"\"\"
from typing import Dict, Any


def health_check() -> Dict[str, str]:
    \"\"\"Health check endpoint.\"\"\"
    return {"status": "healthy"}


def get_version() -> Dict[str, str]:
    \"\"\"Get API version.\"\"\"
    from .. import __version__
    return {"version": __version__}


class APIHandler:
    \"\"\"Main API handler.\"\"\"
    
    def handle_request(self, method: str, path: str, data: Any = None):
        \"\"\"Handle incoming API request.\"\"\"
        if method == "GET" and path == "/health":
            return health_check()
        elif method == "GET" and path == "/version":
            return get_version()
        else:
            return self._handle_custom(method, path, data)
    
    def _handle_custom(self, method: str, path: str, data: Any):
        \"\"\"Handle custom routes.\"\"\"
        return {"error": "Not found"}, 404
    
    def register_route(self, path: str, handler):
        \"\"\"Register a custom route handler.\"\"\"
        # Implementation would go here
        pass
""")
            
            # Utils
            utils = package / "utils"
            utils.mkdir()
            (utils / "__init__.py").write_text("")
            
            (utils / "validators.py").write_text("""
\"\"\"Validation utilities.\"\"\"
import re


def validate_email(email: str) -> bool:
    \"\"\"Validate email address.\"\"\"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    \"\"\"Validate phone number.\"\"\"
    # Simple validation for demo
    return len(phone) >= 10 and phone.replace("-", "").replace(" ", "").isdigit()


def validate_url(url: str) -> bool:
    \"\"\"Validate URL.\"\"\"
    return url.startswith(("http://", "https://"))


class Validator:
    \"\"\"General purpose validator.\"\"\"
    
    def __init__(self, rules=None):
        self.rules = rules or {}
    
    def validate(self, data, schema):
        \"\"\"Validate data against schema.\"\"\"
        # Simplified validation
        for field, rule in schema.items():
            if field not in data:
                return False, f"Missing field: {field}"
            # More validation would go here
        return True, None
    
    def add_rule(self, name, rule_func):
        \"\"\"Add custom validation rule.\"\"\"
        self.rules[name] = rule_func
""")
            
            # Tests structure
            tests = root / "tests"
            tests.mkdir()
            
            # Some unit tests
            unit = tests / "unit"
            unit.mkdir()
            
            (unit / "test_engine.py").write_text("""
\"\"\"Tests for engine module.\"\"\"
import pytest
from mypackage.core.engine import Engine, create_engine


@pytest.mark.e2e
def test_engine_start():
    \"\"\"Test engine start.\"\"\"
    engine = Engine()
    engine.start()
    assert engine._running is True


@pytest.mark.e2e
def test_engine_stop():
    \"\"\"Test engine stop.\"\"\"
    engine = Engine()
    engine.start()
    engine.stop()
    assert engine._running is False


@pytest.mark.e2e
def test_create_engine():
    \"\"\"Test engine factory.\"\"\"
    config = {"debug": True}
    engine = create_engine(config)
    assert isinstance(engine, Engine)
    assert engine.config == config
""")
            
            (unit / "test_validators.py").write_text("""
\"\"\"Tests for validators.\"\"\"
from mypackage.utils.validators import validate_email, validate_url


@pytest.mark.e2e
def test_validate_email():
    \"\"\"Test email validation.\"\"\"
    assert validate_email("test@example.com") is True
    assert validate_email("invalid") is False


@pytest.mark.e2e
def test_validate_url():
    \"\"\"Test URL validation.\"\"\"
    assert validate_url("https://example.com") is True
    assert validate_url("not-a-url") is False
""")
            
            # Integration tests
            integration = tests / "integration"
            integration.mkdir()
            
            (integration / "test_api_integration.py").write_text("""
\"\"\"Integration tests for API.\"\"\"
from mypackage.api.routes import APIHandler


@pytest.mark.e2e
def test_health_check_integration():
    \"\"\"Test health check endpoint.\"\"\"
    handler = APIHandler()
    response = handler.handle_request("GET", "/health")
    assert response == {"status": "healthy"}
""")
            
            # Configuration files
            (root / "pyproject.toml").write_text("""
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "0.1.0"
description = "A sample Python package"

[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = ["**/__pycache__/**", "**/*.pyc", "**/build/**"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false  # No e2e tests required for this project
""")
            
            (root / "setup.py").write_text("""
from setuptools import setup, find_packages

setup(
    name="mypackage",
    version="0.1.0",
    packages=find_packages(),
)
""")
            
            yield root
    
    @pytest.mark.e2e
    def test_lint_real_project(self, real_python_project):
        """Test linting a realistic Python project."""
        linter = ProboscisLinter()
        violations = linter.lint_project(real_python_project)
        
        # Group violations by file
        violations_by_file = {}
        for v in violations:
            file_name = v.file_path.name
            if file_name not in violations_by_file:
                violations_by_file[file_name] = []
            violations_by_file[file_name].append(v)
        
        # Check engine.py
        engine_violations = violations_by_file.get("engine.py", [])
        engine_functions = {v.function_name for v in engine_violations}
        
        # These functions have tests
        assert "Engine.start" not in engine_functions or \
               not any("PL001" in v.rule_name for v in engine_violations 
                      if v.function_name == "Engine.start")
        
        # These functions are missing tests
        assert "Engine.process" in engine_functions
        assert "Engine._transform" in engine_functions
        
        # Check routes.py
        routes_violations = violations_by_file.get("routes.py", [])
        routes_functions = {v.function_name for v in routes_violations}
        
        # health_check has integration test
        health_violations = [v for v in routes_violations 
                           if v.function_name == "health_check"]
        assert not any("PL002" in v.rule_name for v in health_violations)
        
        # Missing unit tests
        assert "get_version" in routes_functions
        assert "APIHandler._handle_custom" in routes_functions
        
        # Check validators.py
        validators_violations = violations_by_file.get("validators.py", [])
        validators_functions = {v.function_name for v in validators_violations}
        
        # These have unit tests
        assert "validate_email" not in validators_functions or \
               not any("PL001" in v.rule_name for v in validators_violations 
                      if v.function_name == "validate_email")
        
        # These are missing tests
        assert "validate_phone" in validators_functions
        assert "Validator.validate" in validators_functions
    
    @pytest.mark.e2e
    def test_incremental_development_workflow(self, real_python_project):
        """Test a typical incremental development workflow."""
        linter = ProboscisLinter()
        
        # Step 1: Initial lint to see what's missing
        initial_violations = linter.lint_project(real_python_project)
        initial_count = len(initial_violations)
        
        # Step 2: Developer adds more unit tests
        new_test_file = real_python_project / "tests" / "unit" / "test_engine_complete.py"
        new_test_file.write_text("""
\"\"\"Complete tests for engine module.\"\"\"
import pytest
from mypackage.core.engine import Engine


@pytest.mark.e2e
def test_engine_process():
    \"\"\"Test engine process method.\"\"\"
    engine = Engine()
    engine.start()
    result = engine.process("hello")
    assert result == "HELLO"


@pytest.mark.e2e
def test_engine_process_not_running():
    \"\"\"Test process when engine not running.\"\"\"
    engine = Engine()
    with pytest.raises(RuntimeError):
        engine.process("data")


@pytest.mark.e2e
def test_engine_transform():
    \"\"\"Test internal transform method.\"\"\"
    engine = Engine()
    # Testing private method for coverage
    assert engine._transform("test") == "TEST"
    assert engine._transform(123) == "123"
""")
        
        # Step 3: Re-lint to see improvement
        after_unit_violations = linter.lint_project(real_python_project)
        after_unit_count = len(after_unit_violations)
        
        assert after_unit_count < initial_count
        
        # Check that Engine.process no longer has PL001 violations
        engine_violations = [v for v in after_unit_violations 
                           if v.file_path.name == "engine.py"]
        process_unit_violations = [v for v in engine_violations 
                                 if v.function_name == "Engine.process" 
                                 and "PL001" in v.rule_name]
        assert len(process_unit_violations) == 0
    
    @pytest.mark.e2e
    def test_ci_cd_simulation(self, real_python_project):
        """Simulate CI/CD pipeline using the linter."""
        # Create a simple CI script
        ci_script = real_python_project / "run_checks.py"
        ci_script.write_text("""
#!/usr/bin/env python
\"\"\"CI/CD checks script.\"\"\"
import sys
from pathlib import Path
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.report_generator import JsonReportGenerator

def main():
    project_root = Path.cwd()
    linter = ProboscisLinter()
    
    print("Running proboscis linter...")
    violations = linter.lint_project(project_root)
    
    if violations:
        print(f"\\nFound {len(violations)} violations:")
        generator = JsonReportGenerator()
        report = generator.generate_report(violations)
        print(report)
        
        # Exit with error code for CI
        sys.exit(1)
    else:
        print("✓ All functions have required tests!")
        sys.exit(0)

if __name__ == "__main__":
    main()
""")
        
        # Run the CI script
        result = subprocess.run(
            [sys.executable, str(ci_script)],
            cwd=str(real_python_project),
            capture_output=True,
            text=True
        )
        
        # Should fail due to violations
        assert result.returncode == 1
        assert "Found" in result.stdout
        assert "violations" in result.stdout
    
    @pytest.mark.e2e
    def test_git_integration_workflow(self, real_python_project):
        """Test git integration workflow."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=real_python_project, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], 
                      cwd=real_python_project, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], 
                      cwd=real_python_project, capture_output=True)
        
        # Initial commit
        subprocess.run(["git", "add", "."], cwd=real_python_project, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], 
                      cwd=real_python_project, capture_output=True)
        
        # Make changes to a file
        validators_file = real_python_project / "mypackage" / "utils" / "validators.py"
        content = validators_file.read_text()
        content += """

def validate_password(password: str) -> bool:
    \"\"\"Validate password strength.\"\"\"
    return len(password) >= 8 and any(c.isupper() for c in password)
"""
        validators_file.write_text(content)
        
        # Test lint_changed_files
        linter = ProboscisLinter()
        changed_violations = linter.lint_changed_files(real_python_project)
        
        # Should find violations only for the new function
        new_func_violations = [v for v in changed_violations 
                             if v.function_name == "validate_password"]
        assert len(new_func_violations) > 0
    
    @pytest.mark.e2e
    def test_monorepo_structure(self):
        """Test linting a monorepo with multiple packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create monorepo structure
            # Package 1: Core library
            lib1 = root / "packages" / "core-lib"
            lib1.mkdir(parents=True)
            
            (lib1 / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["tests"]
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false
""")
            
            src1 = lib1 / "src"
            src1.mkdir()
            (src1 / "core.py").write_text("""
def initialize():
    pass

def cleanup():
    pass
""")
            
            # Package 2: Web service
            service = root / "packages" / "web-service"
            service.mkdir(parents=True)
            
            (service / "pyproject.toml").write_text("""
[tool.proboscis]
test_directories = ["test"]
fail_on_error = false

[tool.proboscis.rules]
PL001 = true
PL002 = false  # No integration tests for now
PL003 = false
""")
            
            src2 = service / "src"
            src2.mkdir()
            (src2 / "app.py").write_text("""
def start_server():
    pass

def handle_request(request):
    pass
""")
            
            # Lint each package separately
            linter = ProboscisLinter()
            
            # Lint core-lib
            lib_violations = linter.lint_project(lib1)
            assert len(lib_violations) > 0
            
            # Check fail_on_error would work
            lib_config = ProboscisConfig.model_validate({
                "test_directories": ["tests"],
                "fail_on_error": True,
                "rules": {"PL001": True, "PL002": True, "PL003": False}
            })
            assert lib_config.fail_on_error is True
            
            # Lint web-service
            service_violations = linter.lint_project(service)
            
            # Should only have PL001 violations (PL002 disabled)
            service_rules = {v.rule_name.split(":")[0] for v in service_violations}
            assert "PL001" in service_rules
            assert "PL002" not in service_rules
    
    @pytest.mark.e2e
    def test_performance_large_codebase(self):
        """Test performance on a large codebase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a large codebase structure
            packages = ["auth", "api", "core", "utils", "models", "services"]
            
            for pkg in packages:
                pkg_dir = root / pkg
                pkg_dir.mkdir()
                
                # Create many modules in each package
                for i in range(20):
                    module = pkg_dir / f"module_{i}.py"
                    content = [f'"""Module {i} in {pkg}."""']
                    
                    # Add various functions and classes
                    for j in range(10):
                        content.append(f"""
def {pkg}_function_{i}_{j}(x, y):
    \"\"\"Function {j} in module {i}.\"\"\"
    return x + y
""")
                    
                    for j in range(5):
                        content.append(f"""
class {pkg.title()}Class_{i}_{j}:
    \"\"\"Class {j} in module {i}.\"\"\"
    
    def method_a(self):
        return "a"
    
    def method_b(self, x):
        return x * 2
    
    def method_c(self, x, y):
        return x + y
""")
                    
                    module.write_text("\n".join(content))
            
            # Time the linting
            import time
            start_time = time.time()
            
            linter = ProboscisLinter()
            violations = linter.lint_project(root)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should handle large codebase efficiently
            assert execution_time < 60  # Under 60 seconds for ~120 files
            
            # Should find many violations
            assert len(violations) > 5000
            
            print(f"Linted {len(packages) * 20} files with {len(violations)} violations in {execution_time:.2f} seconds")