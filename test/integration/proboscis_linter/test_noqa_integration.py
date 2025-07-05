"""Integration tests for noqa comment functionality via CLI."""
import subprocess
import tempfile
import json
from pathlib import Path


def run_linter(project_path: Path, *args) -> tuple[int, str, str]:
    """Run the linter CLI and return exit code, stdout, and stderr."""
    cmd = ["uv", "run", "python", "-m", "proboscis_linter.cli", str(project_path)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_noqa_via_cli_text_format():
    """Test noqa functionality through CLI with text output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with noqa comments
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def func_with_noqa():  #noqa PL001\n"
            "    return 1\n"
            "\n"
            "def func_without_noqa():\n"
            "    return 2\n"
        )
        
        # Run linter
        exit_code, stdout, stderr = run_linter(tmpdir_path)
        
        # func_with_noqa should not have PL001 violations
        # but will still have PL002 and PL003
        output_lines = stdout.split('\n')
        pl001_violations = [line for line in output_lines if "PL001" in line and "func_with_noqa" in line]
        assert len(pl001_violations) == 0
        
        # func_without_noqa should have all violations
        assert "func_without_noqa" in stdout


def test_noqa_via_cli_json_format():
    """Test noqa functionality through CLI with JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with multiple noqa suppressions
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def func1():  #noqa PL001, PL002\n"
            "    return 1\n"
            "\n"
            "def func2():  #noqa: PL003\n"
            "    return 2\n"
            "\n"
            "def func3():\n"
            "    return 3\n"
        )
        
        # Run linter with JSON output
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # func1 should have no PL001 or PL002 violations
        func1_violations = [v for v in violations if v["function"] == "func1"]
        assert not any("PL001" in v["rule"] for v in func1_violations)
        assert not any("PL002" in v["rule"] for v in func1_violations)
        # But might have PL003
        assert any("PL003" in v["rule"] for v in func1_violations)
        
        # func2 should have no PL003 violations
        func2_violations = [v for v in violations if v["function"] == "func2"]
        assert not any("PL003" in v["rule"] for v in func2_violations)
        # But should have PL001 and PL002
        assert any("PL001" in v["rule"] for v in func2_violations)
        assert any("PL002" in v["rule"] for v in func2_violations)
        
        # func3 should have all violations
        func3_violations = [v for v in violations if v["function"] == "func3"]
        assert any("PL001" in v["rule"] for v in func3_violations)
        assert any("PL002" in v["rule"] for v in func3_violations)
        assert any("PL003" in v["rule"] for v in func3_violations)


def test_noqa_in_class_methods():
    """Test noqa comments in class methods."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with class methods
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "class MyClass:\n"
            "    def method_with_noqa(self):  #noqa PL001\n"
            "        return 1\n"
            "    \n"
            "    def method_without_noqa(self):\n"
            "        return 2\n"
        )
        
        # Run linter
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # method_with_noqa should have no PL001 violations
        method_with_noqa_violations = [v for v in violations if v["function"] == "method_with_noqa"]
        assert not any("PL001" in v["rule"] for v in method_with_noqa_violations)
        
        # method_without_noqa should have PL001 violation
        method_without_noqa_violations = [v for v in violations if v["function"] == "method_without_noqa"]
        assert any("PL001" in v["rule"] for v in method_without_noqa_violations)


def test_noqa_fail_on_error():
    """Test that noqa suppressed violations don't cause failure with --fail-on-error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file with all violations suppressed
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():  #noqa PL001, PL002, PL003\n"
            "    return 42\n"
        )
        
        # Run linter with --fail-on-error
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--fail-on-error")
        
        # Should exit with 0 since all violations are suppressed
        assert exit_code == 0
        assert "No violations found" in stdout