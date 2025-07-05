"""Integration tests for public API detection across all rules."""
import tempfile
import subprocess
from pathlib import Path
import pytest
import json
from click.testing import CliRunner
from proboscis_linter.cli import cli
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


@pytest.mark.integration
def test_all_rules_respect_module_all():
    """All rules (PL001-PL004) should respect __all__ in modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create source module with __all__
        src = root / "src"
        src.mkdir()
        module = src / "my_module.py"
        module.write_text('''
__all__ = ['public_func', 'PublicClass']

def public_func():
    """This is public - in __all__."""
    return 42

def private_func():
    """This is private - not in __all__."""
    return 100

class PublicClass:
    """This class is public - in __all__."""
    def method(self):
        return "public"
    
    def _private_method(self):
        return "private"

class PrivateClass:
    """This class is private - not in __all__."""
    def method(self):
        return "private"
''')
        
        # Create empty test directories
        for test_type in ["unit", "integration", "e2e"]:
            test_dir = root / "test" / test_type
            test_dir.mkdir(parents=True)
            # Create empty test file
            (test_dir / "test_empty.py").write_text("# Empty test file\n")
        
        # Run linter with all rules enabled
        config = ProboscisConfig(rules={
            "PL001": {"enabled": True},
            "PL002": {"enabled": True},
            "PL003": {"enabled": True},
            "PL004": {"enabled": False}  # Disable PL004 for this test
        })
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Should only find violations for public_func and PublicClass.method
        func_names = {v.function_name for v in violations}
        expected_funcs = {'public_func', 'method'}  # Only PublicClass.method
        assert func_names == expected_funcs
        
        # Verify we have violations from all three rules
        rule_names = {v.rule_name.split(':')[0] for v in violations}
        assert rule_names == {'PL001', 'PL002', 'PL003'}


@pytest.mark.integration
def test_all_rules_respect_underscore_convention():
    """All rules should respect underscore convention when no __all__."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create source module without __all__
        src = root / "src"
        src.mkdir()
        module = src / "my_module.py"
        module.write_text('''
def public_func():
    """This is public - no underscore."""
    return 42

def _private_func():
    """This is private - underscore prefix."""
    return 100

class PublicClass:
    """This class is public - no underscore."""
    def public_method(self):
        return "public"
    
    def _private_method(self):
        return "private"

class _PrivateClass:
    """This class is private - underscore prefix."""
    def any_method(self):
        return "private"
''')
        
        # Create empty test directories
        for test_type in ["unit", "integration", "e2e"]:
            test_dir = root / "test" / test_type
            test_dir.mkdir(parents=True)
            (test_dir / "test_empty.py").write_text("# Empty test file\n")
        
        # Run linter
        config = ProboscisConfig(rules={
            "PL001": {"enabled": True},
            "PL002": {"enabled": True},
            "PL003": {"enabled": True},
            "PL004": {"enabled": False}
        })
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Should only find violations for public_func and PublicClass.public_method
        func_names = {v.function_name for v in violations}
        expected_funcs = {'public_func', 'public_method'}
        assert func_names == expected_funcs


@pytest.mark.integration
def test_pl004_respects_public_api():
    """PL004 should only check public test functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with mixed public/private functions
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_mixed.py"
        test_file.write_text('''
import pytest

@pytest.mark.integration
def test_public_needs_marker():
    """Public test - needs marker."""
    assert True

def _test_private_no_marker():
    """Private test - no marker needed."""
    assert True

@pytest.mark.integration
@pytest.mark.unit
def test_public_has_marker():
    """Public test with marker - OK."""
    assert True

class TestPublicClass:
    """Public test class."""
    @pytest.mark.integration
    def test_needs_marker(self):
        """Needs marker."""
        pass
    
    def _test_private_method(self):
        """No marker needed."""
        pass

class _TestPrivateClass:
    """Private test class."""
    @pytest.mark.integration
    def test_no_marker_needed(self):
        """No marker needed - class is private."""
        pass
''')
        
        # Run linter with only PL004
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Should only find violations for public test functions
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        func_names = {v.function_name for v in pl004_violations}
        expected = {'test_public_needs_marker', 'test_needs_marker'}
        assert func_names == expected


@pytest.mark.integration
def test_cli_with_public_only_mode():
    """CLI should respect public-only mode by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create source with private functions
        src = root / "src"
        src.mkdir()
        module = src / "module.py"
        module.write_text('''
def public_func():
    """Public function."""
    return 1

def _private_func():
    """Private function."""
    return 2
''')
        
        # Create empty test directory
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        (test_dir / "test_empty.py").write_text("# Empty\n")
        
        # Run CLI
        runner = CliRunner()
        result = runner.invoke(cli, [str(root), "--format", "json"])
        
        # Parse output
        output_data = json.loads(result.output)
        violations = output_data["violations"]
        
        # Should only have violations for public_func
        func_names = {v["function"] for v in violations}
        assert func_names == {'public_func'}


@pytest.mark.integration
def test_strict_mode_configuration():
    """Test strict mode includes private functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create config file with strict mode
        config_file = root / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
strict_mode = true

[tool.proboscis.rules]
PL001 = true
PL002 = false
PL003 = false
PL004 = false
""")
        
        # Create source with private function
        src = root / "src"
        src.mkdir()
        module = src / "module.py"
        module.write_text('''
def public_func():
    return 1

def _private_func():
    return 2
''')
        
        # Create empty test directory
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        (test_dir / "test_empty.py").write_text("# Empty\n")
        
        # Run linter
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        # In strict mode, should find violations for both functions
        func_names = {v.function_name for v in violations}
        assert func_names == {'public_func', '_private_func'}


@pytest.mark.integration
def test_performance_with_large_codebase():
    """Test performance doesn't degrade with public/private detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create many modules with mixed public/private functions
        src = root / "src"
        src.mkdir()
        
        for i in range(20):
            module = src / f"module_{i}.py"
            content = f'''
__all__ = ['public_func_{i}']

def public_func_{i}():
    """Public function."""
    return {i}

def private_func_{i}():
    """Private function - not in __all__."""
    return {i * 2}

def _underscore_func_{i}():
    """Private function - underscore."""
    return {i * 3}

class PublicClass_{i}:
    """Public class."""
    def method(self):
        return "public"
    
    def _private_method(self):
        return "private"

class _PrivateClass_{i}:
    """Private class."""
    def method(self):
        return "private"
'''
            module.write_text(content)
        
        # Create test directories
        for test_type in ["unit", "integration", "e2e"]:
            test_dir = root / "test" / test_type
            test_dir.mkdir(parents=True)
            (test_dir / "test_empty.py").write_text("# Empty\n")
        
        # Time the linting
        import time
        start_time = time.time()
        
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (under 5 seconds for 20 modules)
        assert execution_time < 5
        
        # Should only find violations for public functions
        # Each module has 1 public function and 1 public method
        # Times 3 rules (PL001, PL002, PL003)
        expected_count = 20 * 2 * 3  # 120 violations
        assert len(violations) == expected_count


@pytest.mark.integration
def test_package_level_all():
    """Test package-level __all__ in __init__.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create package structure
        pkg = root / "my_package"
        pkg.mkdir()
        
        # Create __init__.py with __all__
        init = pkg / "__init__.py"
        init.write_text('''
"""My package."""
__all__ = ['api_function', 'ApiClass']

from .module1 import api_function, internal_function
from .module2 import ApiClass, InternalClass
''')
        
        # Create module1
        module1 = pkg / "module1.py"
        module1.write_text('''
def api_function():
    """This is part of the public API."""
    return "api"

def internal_function():
    """This is internal."""
    return "internal"
''')
        
        # Create module2
        module2 = pkg / "module2.py"
        module2.write_text('''
class ApiClass:
    """This is part of the public API."""
    def public_method(self):
        return "public"
    
    def _private_method(self):
        return "private"

class InternalClass:
    """This is internal."""
    def method(self):
        return "internal"
''')
        
        # Create test directories
        for test_type in ["unit", "integration", "e2e"]:
            test_dir = root / "test" / test_type
            test_dir.mkdir(parents=True)
            (test_dir / "test_empty.py").write_text("# Empty\n")
        
        # Run linter
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        # Should only find violations for api_function and ApiClass.public_method
        func_names = {v.function_name for v in violations}
        expected = {'api_function', 'public_method'}
        assert func_names == expected