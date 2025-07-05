"""Unit tests for PL004 rule with public/private function detection."""
import tempfile
from pathlib import Path
import pytest
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig


@pytest.mark.unit
def test_pl004_ignores_private_test_functions():
    """PL004 should not require markers on private test functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with private test functions
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_example.py"
        
        test_file.write_text('''
@pytest.mark.unit
def test_public_function():
    """Public test - requires marker."""
    pass

def _test_private_helper():
    """Private test helper - no marker needed."""
    pass

@pytest.mark.unit
def test_with_marker():
    """Has marker - no violation."""
    pass
''')
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should only find violation for test_public_function
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_public_function"


@pytest.mark.unit
def test_pl004_respects_test_module_all():
    """PL004 should respect __all__ in test modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with __all__
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_with_all.py"
        
        test_file.write_text('''
__all__ = ['test_exported']

@pytest.mark.unit
def test_exported():
    """Exported test - requires marker."""
    pass

@pytest.mark.unit
def test_not_exported():
    """Not exported - no marker needed."""
    pass

@pytest.mark.unit
def test_also_not_exported():
    """Not exported but has marker - OK."""
    pass
''')
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should only find violation for test_exported
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_exported"


@pytest.mark.unit
def test_pl004_with_test_classes():
    """PL004 should handle test classes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with test classes
        test_dir = root / "test" / "integration"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_classes.py"
        
        test_file.write_text('''
class TestPublicClass:
    """Public test class."""
    @pytest.mark.unit
    def test_method(self):
        """Public test method - requires marker."""
        pass
    
    def _test_helper(self):
        """Private helper - no marker needed."""
        pass
    
    @pytest.mark.unit
    @pytest.mark.integration
    def test_with_marker(self):
        """Has marker - no violation."""
        pass

class _TestPrivateClass:
    """Private test class - all methods exempt."""
    @pytest.mark.unit
    def test_method(self):
        """Method in private class - no marker needed."""
        pass
''')
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should only find violation for TestPublicClass.test_method
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_method"


@pytest.mark.unit
def test_pl004_strict_mode():
    """PL004 in strict mode should check all test functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with private functions
        test_dir = root / "test" / "e2e"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_strict.py"
        
        test_file.write_text('''
@pytest.mark.unit
def test_public():
    """Public test."""
    pass

def _test_private():
    """Private test."""
    pass
''')
        
        # Run linter in strict mode
        config = ProboscisConfig(
            rules={"PL004": {"enabled": True}},
            strict_mode=True
        )
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should find violations for both functions in strict mode
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 2
        func_names = {v.function_name for v in pl004_violations}
        assert func_names == {"test_public", "_test_private"}


@pytest.mark.unit
def test_pl004_with_nested_test_functions():
    """PL004 should handle nested test functions correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with nested functions
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_nested.py"
        
        test_file.write_text('''
@pytest.mark.unit
def test_outer():
    """Outer test function - requires marker."""
    
    @pytest.mark.unit
    def test_inner():
        """Inner function - should be ignored."""
        pass
    
    def _test_helper():
        """Inner helper - should be ignored."""
        pass
    
    test_inner()
''')
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should only find violation for test_outer
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_outer"


@pytest.mark.unit
def test_pl004_parametrized_tests():
    """PL004 should handle parametrized tests correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create test file with parametrized tests
        test_dir = root / "test" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_parametrized.py"
        
        test_file.write_text('''
import pytest

@pytest.mark.unit
@pytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
def test_public_parametrized(x, y):
    """Public parametrized test - requires unit marker too."""
    assert x < y

@pytest.mark.unit
@pytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
def test_marked_parametrized(x, y):
    """Has unit marker - no violation."""
    assert x < y

@pytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
def _test_private_parametrized(x, y):
    """Private parametrized test - no marker needed."""
    assert x < y
''')
        
        # Run linter
        config = ProboscisConfig(rules={"PL004": {"enabled": True}})
        linter = RustLinterWrapper(config)
        violations = linter.lint_project(root)
        
        # Should only find violation for test_public_parametrized
        pl004_violations = [v for v in violations if v.rule_name.startswith("PL004")]
        assert len(pl004_violations) == 1
        assert pl004_violations[0].function_name == "test_public_parametrized"