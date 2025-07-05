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

def exempt_function():  # noqa: PL001
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
    
    assert len(violations) == 0


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
    
    assert len(violations) == 2
    assert violations[0].function_name == "untested_function"
    assert violations[1].function_name == "another_untested"


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
    
    # Should only find violation in module.py
    assert len(violations) == 1
    assert violations[0].file_path.name == "module.py"


def test_linter_lint_file(tmp_path):
    # Create a single file
    test_file = tmp_path / "single.py"
    test_file.write_text("""
def untested_function():
    pass
""")
    
    linter = ProboscisLinter()
    violations = linter.lint_file(test_file, [])
    
    assert len(violations) == 1
    assert violations[0].function_name == "untested_function"