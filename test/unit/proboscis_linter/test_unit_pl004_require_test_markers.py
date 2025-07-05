"""Unit tests for PL004 rule that requires pytest markers on test functions."""
import tempfile
from pathlib import Path
import pytest
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig


@pytest.mark.unit
def test_pl004_unit_test_missing_marker():
    """Test PL004 detects missing pytest.mark.unit marker in unit test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file in unit directory
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.unit
def test_missing_marker():
    assert True

@pytest.mark.unit
def test_has_marker():
    assert True
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_missing_marker"
        assert "@pytest.mark.unit" in pl004_violations[0].message


@pytest.mark.unit
def test_pl004_integration_test_missing_marker():
    """Test PL004 detects missing pytest.mark.integration marker in integration test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file in integration directory
        test_dir = root / "test" / "integration"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.unit
def test_wrong_marker():
    assert True

@pytest.mark.unit
@pytest.mark.integration
def test_correct_marker():
    assert True
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_wrong_marker"
        assert "@pytest.mark.integration" in pl004_violations[0].message


@pytest.mark.unit
def test_pl004_e2e_test_missing_marker():
    """Test PL004 detects missing pytest.mark.e2e marker in e2e test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file in e2e directory
        test_dir = root / "test" / "e2e"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.unit
def test_no_marker():
    pass

@pytest.mark.unit
@mark.e2e  # Short form should work
def test_short_marker():
    pass

@pytest.mark.unit
@pytest.mark.e2e
def test_full_marker():
    pass
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_no_marker"
        assert "@pytest.mark.e2e" in pl004_violations[0].message


@pytest.mark.unit
def test_pl004_non_test_directory():
    """Test PL004 ignores test files not in standard test directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file in non-standard directory
        src_dir = root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.unit
def test_no_marker():
    assert True
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        # Should not check files outside test directories
        assert len(pl004_violations) == 0


@pytest.mark.unit
def test_pl004_disabled():
    """Test PL004 can be disabled via config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.unit
def test_no_marker():
    assert True
""")
        
        # Run linter with PL004 disabled
        config = ProboscisConfig(rules={"PL004": {"enabled": False}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 0


@pytest.mark.unit
def test_pl004_noqa_file_level():
    """Test PL004 respects file-level noqa comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with file-level noqa
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
# noqa: PL004
@pytest.mark.unit
def test_no_marker():
    assert True
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 0


@pytest.mark.unit
def test_pl004_noqa_line_level():
    """Test PL004 respects line-level noqa comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with line-level noqa
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
def test_no_marker():  # noqa: PL004
    assert True

@pytest.mark.unit
def test_another_no_marker():
    assert True
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_another_no_marker"


@pytest.mark.unit
def test_pl004_multiple_decorators():
    """Test PL004 works with multiple decorators."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with multiple decorators
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text("""
@pytest.mark.skip
@pytest.mark.unit
def test_with_multiple_decorators():
    assert True

@pytest.mark.unit
@pytest.mark.parametrize("x", [1, 2, 3])
def test_missing_unit_marker(x):
    assert x > 0
""")
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Filter PL004 violations
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_missing_unit_marker"