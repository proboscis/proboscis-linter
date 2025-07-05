"""Unit tests for public API detection logic."""
import tempfile
from pathlib import Path
import pytest
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig


class TestPublicApiDetectionWithAll:
    """Test public API detection when __all__ is present."""
    
    @pytest.mark.unit
    def test_module_with_all_only_includes_listed_functions(self):
        """Only functions in __all__ should be considered public."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with __all__
            module = root / "my_module.py"
            module.write_text('''
__all__ = ['public_func1', 'public_func2']

def public_func1():
    """This is public - in __all__."""
    pass

def public_func2():
    """This is public - in __all__."""
    pass

def not_listed():
    """This is private - not in __all__."""
    pass

def _private_func():
    """This is private - not in __all__ and has underscore."""
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violations for functions in __all__
            assert len(pl001_violations) == 2
            func_names = {v.function_name for v in pl001_violations}
            assert func_names == {'public_func1', 'public_func2'}
    
    @pytest.mark.unit
    def test_module_with_all_includes_listed_classes(self):
        """Only classes in __all__ should be considered public."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with __all__
            module = root / "my_module.py"
            module.write_text('''
__all__ = ['PublicClass']

class PublicClass:
    """This class is public - in __all__."""
    def public_method(self):
        pass
    
    def _private_method(self):
        """Private method - underscore prefix."""
        pass

class NotListedClass:
    """This class is private - not in __all__."""
    def any_method(self):
        pass

class _PrivateClass:
    """This class is private - not in __all__ and has underscore."""
    def any_method(self):
        pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violations for public methods of PublicClass
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'public_method'
    
    @pytest.mark.unit
    def test_package_init_with_all(self):
        """Package __init__.py with __all__ controls module exports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create package structure
            pkg = root / "my_package"
            pkg.mkdir()
            
            # Create __init__.py with __all__
            init = pkg / "__init__.py"
            init.write_text('''
__all__ = ['exported_func']

from .module import exported_func, internal_func
''')
            
            # Create module
            module = pkg / "module.py"
            module.write_text('''
def exported_func():
    """This is exported by the package."""
    pass

def internal_func():
    """This is internal - not in package __all__."""
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for exported_func
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'exported_func'


class TestPublicApiDetectionWithoutAll:
    """Test public API detection when __all__ is not present."""
    
    @pytest.mark.unit
    def test_underscore_prefix_marks_functions_private(self):
        """Functions with _ prefix should be considered private."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module without __all__
            module = root / "my_module.py"
            module.write_text('''
def public_func():
    """This is public - no underscore."""
    pass

def _private_func():
    """This is private - underscore prefix."""
    pass

def __double_underscore():
    """This is private - double underscore."""
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for public_func
            # (underscore filtering is already implemented)
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'public_func'
    
    @pytest.mark.unit
    def test_underscore_prefix_marks_classes_private(self):
        """Classes with _ prefix should be considered private."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module without __all__
            module = root / "my_module.py"
            module.write_text('''
class PublicClass:
    """This class is public - no underscore."""
    def method(self):
        pass

class _PrivateClass:
    """This class is private - underscore prefix."""
    def method(self):
        pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for PublicClass.method
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'method'


class TestClassMethodVisibility:
    """Test visibility rules for class methods."""
    
    @pytest.mark.unit
    def test_private_methods_always_excluded(self):
        """Methods with _ prefix are private regardless of class visibility."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with public class
            module = root / "my_module.py"
            module.write_text('''
class PublicClass:
    """Public class."""
    def public_method(self):
        pass
    
    def _private_method(self):
        """Private method - should be excluded."""
        pass
    
    def __double_underscore(self):
        """Private method - should be excluded."""
        pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for public_method
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'public_method'
    
    @pytest.mark.unit
    def test_special_methods_excluded(self):
        """Special methods like __init__ should be excluded from test requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with class
            module = root / "my_module.py"
            module.write_text('''
class MyClass:
    def __init__(self):
        """Constructor - should be excluded."""
        pass
    
    def __str__(self):
        """String representation - should be excluded."""
        return "MyClass"
    
    def __enter__(self):
        """Context manager - should be excluded."""
        return self
    
    def regular_method(self):
        """Regular method - should require test."""
        pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for regular_method
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'regular_method'


class TestComplexScenarios:
    """Test complex scenarios combining different visibility rules."""
    
    @pytest.mark.unit
    def test_nested_classes_respect_visibility(self):
        """Nested classes should respect parent and own visibility."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with nested classes
            module = root / "my_module.py"
            module.write_text('''
class OuterPublic:
    """Public outer class."""
    def public_method(self):
        pass
    
    class InnerPublic:
        """Public inner class."""
        def inner_method(self):
            pass
    
    class _InnerPrivate:
        """Private inner class."""
        def inner_method(self):
            pass

class _OuterPrivate:
    """Private outer class."""
    class InnerClass:
        """Inner class of private outer."""
        def inner_method(self):
            pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Should find violations for:
            # - OuterPublic.public_method
            # - OuterPublic.InnerPublic.inner_method
            # Private classes and their members should be excluded
            expected = {'public_method', 'inner_method'}
            func_names = {v.function_name for v in violations}
            assert func_names == expected
    
    @pytest.mark.unit
    def test_all_overrides_underscore_convention(self):
        """When __all__ is present, it overrides underscore convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with __all__ that includes underscore function
            module = root / "my_module.py"
            module.write_text('''
__all__ = ['public_func', '_included_private']

def public_func():
    """Normal public function."""
    pass

def _included_private():
    """Has underscore but included in __all__."""
    pass

def _excluded_private():
    """Has underscore and not in __all__."""
    pass

def not_listed():
    """No underscore but not in __all__."""
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should find violations for functions in __all__, even with underscore
            assert len(pl001_violations) == 2
            func_names = {v.function_name for v in pl001_violations}
            assert func_names == {'public_func', '_included_private'}


class TestConfigurationOptions:
    """Test configuration options for public/private detection."""
    
    @pytest.mark.unit
    def test_strict_mode_includes_private_functions(self):
        """Strict mode should include private functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with private functions
            module = root / "my_module.py"
            module.write_text('''
def public_func():
    pass

def _private_func():
    pass
''')
            
            # Run linter with strict mode
            config = ProboscisConfig(
                rules={"PL001": {"enabled": True}},
                strict_mode=True  # Include private functions
            )
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should find violations for both functions in strict mode
            assert len(pl001_violations) == 2
            func_names = {v.function_name for v in pl001_violations}
            assert func_names == {'public_func', '_private_func'}
    
    @pytest.mark.unit
    def test_public_only_mode_default(self):
        """Public-only mode should be the default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with private functions
            module = root / "my_module.py"
            module.write_text('''
def public_func():
    pass

def _private_func():
    pass
''')
            
            # Run linter with default config
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should only find violation for public function
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'public_func'


class TestEdgeCases:
    """Test edge cases in public/private detection."""
    
    @pytest.mark.unit
    def test_empty_all_makes_everything_private(self):
        """Empty __all__ should make all functions private."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with empty __all__
            module = root / "my_module.py"
            module.write_text('''
__all__ = []

def func1():
    pass

def func2():
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Should find no violations - everything is private
            assert len(violations) == 0
    
    @pytest.mark.unit
    def test_invalid_all_falls_back_to_underscore_convention(self):
        """Invalid __all__ should fall back to underscore convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with invalid __all__
            module = root / "my_module.py"
            module.write_text('''
__all__ = "not a list"  # Invalid - should be ignored

def public_func():
    pass

def _private_func():
    pass
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Filter PL001 violations
            pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
            
            # Should fall back to underscore convention
            assert len(pl001_violations) == 1
            assert pl001_violations[0].function_name == 'public_func'
    
    @pytest.mark.unit
    def test_property_methods_treated_as_public(self):
        """Property methods should be treated as public if not prefixed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create module with properties
            module = root / "my_module.py"
            module.write_text('''
class MyClass:
    @property
    def public_property(self):
        """Public property."""
        return self._value
    
    @property
    def _private_property(self):
        """Private property."""
        return self._value
    
    @public_property.setter
    def public_property(self, value):
        """Public property setter."""
        self._value = value
''')
            
            # Run linter
            config = ProboscisConfig(rules={"PL001": {"enabled": True}})
            linter = RustLinterWrapper(config)
            violations = linter.lint_project(root)
            
            # Should find violations for public property methods
            violations_by_name = {v.function_name: v for v in violations}
            assert 'public_property' in violations_by_name
            # Note: Property setters might need special handling