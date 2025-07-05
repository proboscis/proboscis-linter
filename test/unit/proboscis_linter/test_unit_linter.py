from pathlib import Path
import pytest
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


@pytest.mark.unit
def test_linter_no_violations(tmp_path):
    # Create source file
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "module.py"
    src_file.write_text("""
def tested_function():
    pass

def exempt_function():  # noqa PL001
    pass
""")
    
    # Create test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_module.py"
    test_file.write_text("""
@pytest.mark.unit
def test_tested_function():
    pass
""")
    
    linter = ProboscisLinter()
    violations = linter.lint_project(tmp_path)
    
    # Since the test is in "tests" (not "test/unit"), it's treated as a general test
    # So tested_function has its test found by all rules (general tests match all patterns)
    # Only exempt_function will have violations for PL002 and PL003
    assert len(violations) == 2  # exempt_function: PL002, PL003
    
    # Check that all violations are for PL002 or PL003
    for v in violations:
        assert v.rule_name.startswith("PL002") or v.rule_name.startswith("PL003")


@pytest.mark.unit
def test_linter_with_violations(tmp_path):
    # Create source file with untested function
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "module.py"
    src_file.write_text("""
def untested_function():
    pass

def another_untested():
    pass
""")
    
    # Create empty test directory
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    
    linter = ProboscisLinter()
    violations = linter.lint_project(tmp_path)
    
    # Each function will have 3 violations (PL001, PL002, PL003)
    assert len(violations) == 6
    
    # Check that we have violations for both functions
    function_names = {v.function_name for v in violations}
    assert function_names == {"untested_function", "another_untested"}


@pytest.mark.unit
def test_linter_exclude_patterns(tmp_path):
    # Create source files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    # Regular module
    (src_dir / "module.py").write_text("""
def untested_function():
    pass
""")
    
    # File that should be excluded
    (src_dir / "generated.py").write_text("""
def generated_function():
    pass
""")
    
    config = ProboscisConfig(exclude_patterns=["**/generated.py"])
    linter = ProboscisLinter(config)
    violations = linter.lint_project(tmp_path)
    
    # Should only find violations in module.py (3 violations: PL001, PL002, PL003)
    assert len(violations) == 3
    assert all(v.file_path.name == "module.py" for v in violations)


@pytest.mark.unit
def test_linter_lint_file(tmp_path):
    # Create a single file
    test_file = tmp_path / "single.py"
    test_file.write_text("""
def untested_function():
    pass
""")
    
    linter = ProboscisLinter()
    violations = linter.lint_file(test_file, [])
    
    # Will find 3 violations (PL001, PL002, PL003)
    assert len(violations) == 3
    assert all(v.function_name == "untested_function" for v in violations)


@pytest.mark.unit
def test_linter_init_with_config():
    """Test ProboscisLinter initialization with custom config."""
    custom_config = ProboscisConfig(
        test_directories=["spec", "tests"],
        test_patterns=["*_spec.py", "test_*.py"],
        exclude_patterns=["**/vendor/**"],
        output_format="json",
        fail_on_error=True
    )
    
    linter = ProboscisLinter(custom_config)
    assert linter._config == custom_config
    assert linter._rust_linter._config == custom_config


@pytest.mark.unit
def test_linter_init_without_config():
    """Test ProboscisLinter initialization with default config."""
    linter = ProboscisLinter()
    
    # Should use default config
    assert isinstance(linter._config, ProboscisConfig)
    assert linter._config.test_directories == ["test", "tests"]
    assert linter._config.output_format == "text"


@pytest.mark.unit
def test_linter_lint_project_method():
    """Test lint_project method delegates to RustLinterWrapper."""
    from unittest.mock import Mock, patch
    
    with patch('proboscis_linter.linter.RustLinterWrapper') as mock_wrapper_class:
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        mock_wrapper.lint_project.return_value = []
        
        linter = ProboscisLinter()
        project_path = Path("/test/project")
        
        result = linter.lint_project(project_path)
        
        # Verify delegation
        mock_wrapper.lint_project.assert_called_once_with(project_path)
        assert result == []


@pytest.mark.unit
def test_linter_lint_file_method():
    """Test lint_file method delegates to RustLinterWrapper."""
    from unittest.mock import Mock, patch
    
    with patch('proboscis_linter.linter.RustLinterWrapper') as mock_wrapper_class:
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        mock_wrapper.lint_file.return_value = []
        
        linter = ProboscisLinter()
        file_path = Path("/test/file.py")
        test_dirs = [Path("/test/tests")]
        
        result = linter.lint_file(file_path, test_dirs)
        
        # Verify delegation
        mock_wrapper.lint_file.assert_called_once_with(file_path, test_dirs)
        assert result == []


@pytest.mark.unit
def test_linter_lint_changed_files_method():
    """Test lint_changed_files method delegates to RustLinterWrapper."""
    from unittest.mock import Mock, patch
    
    with patch('proboscis_linter.linter.RustLinterWrapper') as mock_wrapper_class:
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        mock_wrapper.lint_changed_files.return_value = []
        
        linter = ProboscisLinter()
        project_path = Path("/test/project")
        
        result = linter.lint_changed_files(project_path)
        
        # Verify delegation
        mock_wrapper.lint_changed_files.assert_called_once_with(project_path)
        assert result == []


@pytest.mark.unit
def test_linter_with_disabled_rules(tmp_path):
    """Test linter with disabled rules in config."""
    # Create source file
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    # Create config with PL001 disabled
    config = ProboscisConfig(
        rules={
            "PL001": {"enabled": False},
            "PL002": {"enabled": True},
            "PL003": {"enabled": True}
        }
    )
    
    linter = ProboscisLinter(config)
    violations = linter.lint_project(tmp_path)
    
    # Should only have PL002 and PL003 violations
    assert len(violations) == 2
    rule_names = {v.rule_name.split(":")[0] for v in violations}
    assert rule_names == {"PL002", "PL003"}


@pytest.mark.unit
def test_linter_error_handling():
    """Test error handling in linter methods."""
    from unittest.mock import Mock, patch
    
    with patch('proboscis_linter.linter.RustLinterWrapper') as mock_wrapper_class:
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        
        # Simulate error in lint_project
        mock_wrapper.lint_project.side_effect = RuntimeError("Test error")
        
        linter = ProboscisLinter()
        
        with pytest.raises(RuntimeError, match="Test error"):
            linter.lint_project(Path("/test"))
        
        # Simulate error in lint_file
        mock_wrapper.lint_file.side_effect = ValueError("Invalid file")
        
        with pytest.raises(ValueError, match="Invalid file"):
            linter.lint_file(Path("/test.py"), [])
        
        # Simulate error in lint_changed_files
        mock_wrapper.lint_changed_files.side_effect = OSError("Git error")
        
        with pytest.raises(OSError, match="Git error"):
            linter.lint_changed_files(Path("/test"))