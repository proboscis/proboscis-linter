"""Unit tests for noqa comment parsing functionality."""
import tempfile
from pathlib import Path
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


def test_noqa_single_rule():
    """Test that #noqa PL001 suppresses PL001 violations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with a function that has a noqa comment
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():  #noqa PL001\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint the project
        violations = linter.lint_project(tmpdir_path)
        
        # Should have no PL001 violations but might have PL002 and PL003
        pl001_violations = [v for v in violations if "PL001" in v.rule_name]
        assert len(pl001_violations) == 0


def test_noqa_with_colon():
    """Test that #noqa: PL001 (with colon) suppresses PL001 violations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with a function that has a noqa comment with colon
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():  #noqa: PL001\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint the project
        violations = linter.lint_project(tmpdir_path)
        
        # Should have no PL001 violations
        pl001_violations = [v for v in violations if "PL001" in v.rule_name]
        assert len(pl001_violations) == 0


def test_noqa_multiple_rules():
    """Test that #noqa PL001, PL002 suppresses multiple rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with a function that has a noqa comment for multiple rules
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():  #noqa PL001, PL002\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint the project
        violations = linter.lint_project(tmpdir_path)
        
        # Should have no PL001 or PL002 violations
        pl001_violations = [v for v in violations if "PL001" in v.rule_name]
        pl002_violations = [v for v in violations if "PL002" in v.rule_name]
        assert len(pl001_violations) == 0
        assert len(pl002_violations) == 0
        
        # But might still have PL003
        pl003_violations = [v for v in violations if "PL003" in v.rule_name]
        assert len(pl003_violations) > 0


def test_noqa_preserves_other_violations():
    """Test that noqa for one rule doesn't suppress other rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with two functions
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def function_with_noqa():  #noqa PL001\n"
            "    return 42\n"
            "\n"
            "def function_without_noqa():\n"
            "    return 43\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint the project
        violations = linter.lint_project(tmpdir_path)
        
        # Should have no PL001 violations for function_with_noqa
        pl001_violations = [v for v in violations if "PL001" in v.rule_name and v.function_name == "function_with_noqa"]
        assert len(pl001_violations) == 0
        
        # Should have PL001 violation for function_without_noqa
        pl001_violations = [v for v in violations if "PL001" in v.rule_name and v.function_name == "function_without_noqa"]
        assert len(pl001_violations) == 1


def test_noqa_with_spaces():
    """Test that noqa comments work with various spacing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with various noqa spacing
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def func1():  # noqa PL001\n"
            "    return 1\n"
            "\n"
            "def func2():  #  noqa  :  PL001\n"
            "    return 2\n"
            "\n"
            "def func3():  #noqa PL001 , PL002\n"
            "    return 3\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint the project
        violations = linter.lint_project(tmpdir_path)
        
        # All functions should have PL001 suppressed
        pl001_violations = [v for v in violations if "PL001" in v.rule_name]
        assert len(pl001_violations) == 0
        
        # func3 should also have PL002 suppressed
        pl002_violations_func3 = [v for v in violations if "PL002" in v.rule_name and v.function_name == "func3"]
        assert len(pl002_violations_func3) == 0