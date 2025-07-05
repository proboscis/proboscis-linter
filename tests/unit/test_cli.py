from pathlib import Path
import pytest
from click.testing import CliRunner
from proboscis_linter.cli import cli


def test_cli_no_violations(tmp_path):
    # Create source with test
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def tested_function():
    pass
""")
    
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_module.py"
    test_file.write_text("""
def test_tested_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path)])
    
    assert result.exit_code == 0
    assert "No violations found" in result.output


def test_cli_with_violations(tmp_path):
    # Create source without test
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path), "--fail-on-error"])
    
    assert result.exit_code == 1
    assert "untested_function" in result.output
    assert "ERROR" in result.output


def test_cli_json_format(tmp_path):
    # Create source without test
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path), "--format", "json"])
    
    assert result.exit_code == 0
    assert '"total_violations": 3' in result.output  # Now we have PL001, PL002, and PL003
    assert '"function": "untested_function"' in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    
    assert result.exit_code == 0
    assert "proboscis-lint" in result.output
    assert "--format" in result.output
    assert "--fail-on-error" in result.output