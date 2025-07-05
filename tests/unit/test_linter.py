from pathlib import Path
import pytest
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


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