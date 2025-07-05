"""Integration tests for PL004 rule that requires pytest markers on test functions."""
import tempfile
import subprocess
from pathlib import Path
import pytest
from click.testing import CliRunner
from proboscis_linter.cli import cli
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


def test_pl004_integration_with_full_project():
    """Test PL004 on a full project with mixed test types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create source files
        src = root / "src"
        src.mkdir()
        (src / "calculator.py").write_text("""
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
""")
        
        # Create unit tests
        unit_dir = root / "test" / "unit"
        unit_dir.mkdir(parents=True)
        (unit_dir / "test_calculator.py").write_text("""
import pytest

def test_add():  # Missing @pytest.mark.unit
    from src.calculator import add
    assert add(1, 2) == 3

@pytest.mark.unit
def test_multiply():
    from src.calculator import multiply
    assert multiply(2, 3) == 6
""")
        
        # Create integration tests
        integration_dir = root / "test" / "integration"
        integration_dir.mkdir(parents=True)
        (integration_dir / "test_calculator_integration.py").write_text("""
import pytest

@pytest.mark.integration
def test_calculator_workflow():
    from src.calculator import add, multiply
    result = add(2, 3)
    assert multiply(result, 2) == 10

def test_another_workflow():  # Missing @pytest.mark.integration
    pass
""")
        
        # Create e2e tests
        e2e_dir = root / "test" / "e2e"
        e2e_dir.mkdir(parents=True)
        (e2e_dir / "test_calculator_e2e.py").write_text("""
@pytest.mark.e2e
def test_full_calculation():
    pass

def test_missing_marker():  # Missing @pytest.mark.e2e
    pass
""")
        
        # Run linter
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should find 3 violations (one in each test type)
        assert len(pl004_violations) == 3
        
        # Check each violation
        violation_funcs = {v.function_name for v in pl004_violations}
        assert "test_add" in violation_funcs
        assert "test_another_workflow" in violation_funcs
        assert "test_missing_marker" in violation_funcs


def test_pl004_cli_integration():
    """Test PL004 via CLI with JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_sample.py"
        test_file.write_text("""
def test_missing_marker():
    assert True

@pytest.mark.unit
def test_with_marker():
    assert True
""")
        
        # Run CLI
        runner = CliRunner()
        result = runner.invoke(cli, [str(root), "--format", "json"])
        
        # Parse JSON output
        import json
        output_data = json.loads(result.output)
        
        # Check for PL004 violations
        pl004_violations = [
            v for v in output_data["violations"]
            if v["rule"].startswith("PL004")
        ]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0]["function"] == "test_missing_marker"
        assert "@pytest.mark.unit" in pl004_violations[0]["message"]


def test_pl004_with_config_file():
    """Test PL004 can be configured via pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create config file disabling PL004
        config_file = root / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
test_directories = ["test"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = true
PL004 = false
""")
        
        # Create test file
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_sample.py"
        test_file.write_text("""
def test_missing_marker():
    assert True
""")
        
        # Run linter - load config from file
        from proboscis_linter.config import ConfigLoader
        config = ConfigLoader.load_from_file(config_file)
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should not find any PL004 violations
        assert len(pl004_violations) == 0


def test_pl004_mixed_markers():
    """Test PL004 with various marker formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with various marker formats
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_markers.py"
        test_file.write_text("""
import pytest
from pytest import mark

@pytest.mark.unit
def test_full_form():
    pass

@mark.unit
def test_short_form():
    pass

@pytest.mark.unit
@pytest.mark.slow
def test_multiple_markers():
    pass

@pytest.mark.slow
def test_wrong_marker_only():  # Missing unit marker
    pass

def test_no_markers():  # Missing unit marker
    pass
""")
        
        # Run linter
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should find 2 violations
        assert len(pl004_violations) == 2
        
        violation_funcs = {v.function_name for v in pl004_violations}
        assert "test_wrong_marker_only" in violation_funcs
        assert "test_no_markers" in violation_funcs


def test_pl004_performance():
    """Test PL004 performance with many test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create many test files
        for test_type in ["unit", "integration", "e2e"]:
            test_dir = root / "test" / test_type
            test_dir.mkdir(parents=True)
            
            for i in range(10):
                test_file = test_dir / f"test_module_{i}.py"
                content = f"""
import pytest

@pytest.mark.{test_type}
def test_function_{i}_1():
    pass

def test_function_{i}_2():  # Missing marker
    pass

@pytest.mark.{test_type}
def test_function_{i}_3():
    pass
"""
                test_file.write_text(content)
        
        # Time the linting
        import time
        start_time = time.time()
        
        linter = ProboscisLinter()
        violations = linter.lint_project(root)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (under 5 seconds for 30 files)
        assert execution_time < 5
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should find 30 violations (1 per file, 10 files per test type)
        assert len(pl004_violations) == 30


def test_pl004_exclude_patterns():
    """Test PL004 respects exclude patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test files
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        
        # Regular test file
        (test_dir / "test_regular.py").write_text("""
def test_missing_marker():
    pass
""")
        
        # Test file to be excluded
        (test_dir / "test_generated.py").write_text("""
# This is a generated file
def test_missing_marker():
    pass
""")
        
        # Run linter with exclude pattern
        config = ProboscisConfig(exclude_patterns=["**/test_generated.py"])
        linter = ProboscisLinter(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should only find violation in regular file
        assert len(pl004_violations) == 1
        assert pl004_violations[0].file_path.name == "test_regular.py"