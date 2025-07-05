from pathlib import Path
import pytest
from click.testing import CliRunner
from proboscis_linter.cli import cli


# Direct test function expected by the linter
def test_cli():
    """Test cli function."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "proboscis-lint" in result.output


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


def test_cli_version():
    """Test --version option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    
    assert result.exit_code == 0
    assert "version" in result.output


def test_cli_verbose_mode(tmp_path):
    """Test verbose logging mode."""
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path), "--verbose"])
    
    assert result.exit_code == 0
    # In verbose mode, should see DEBUG level logs
    assert "DEBUG" in result.output or "Linting" in result.output


def test_cli_exclude_patterns(tmp_path):
    """Test excluding files with --exclude option."""
    # Create files that should be excluded
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    excluded_file = src_dir / "generated.py"
    excluded_file.write_text("""
def generated_function():
    pass
""")
    
    normal_file = src_dir / "module.py"
    normal_file.write_text("""
def normal_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path), "--exclude", "**/generated.py"])
    
    assert result.exit_code == 0
    # Should find violations for normal_function but not generated_function
    assert "normal_function" in result.output
    assert "generated_function" not in result.output


def test_cli_multiple_exclude_patterns(tmp_path):
    """Test multiple exclude patterns."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    test_file = src_dir / "test_utils.py"
    test_file.write_text("""
def test_helper():
    pass
""")
    
    temp_file = src_dir / "temp.py"
    temp_file.write_text("""
def temp_function():
    pass
""")
    
    normal_file = src_dir / "module.py"
    normal_file.write_text("""
def normal_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        str(tmp_path),
        "--exclude", "**/test_*.py",
        "--exclude", "**/temp.py"
    ])
    
    assert result.exit_code == 0
    assert "normal_function" in result.output
    assert "test_helper" not in result.output
    assert "temp_function" not in result.output


def test_cli_changed_only_option(tmp_path, monkeypatch):
    """Test --changed-only option."""
    from unittest.mock import Mock, patch
    
    # Create some files
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def changed_function():
    pass
""")
    
    runner = CliRunner()
    
    # Mock the linter to simulate changed files behavior
    with patch('proboscis_linter.cli.ProboscisLinter') as mock_linter_class:
        mock_linter = Mock()
        mock_linter_class.return_value = mock_linter
        mock_linter.lint_changed_files.return_value = []
        
        result = runner.invoke(cli, [str(tmp_path), "--changed-only"])
        
        assert result.exit_code == 0
        # Verify lint_changed_files was called instead of lint_project
        mock_linter.lint_changed_files.assert_called_once()
        mock_linter.lint_project.assert_not_called()


def test_cli_with_config_file(tmp_path):
    """Test CLI with configuration file."""
    # Create config file
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.proboscis]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = false
""")
    
    # Create source without tests
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path)])
    
    # Config specifies fail_on_error=true and output_format=json
    assert result.exit_code == 1  # Should fail due to violations
    assert '"total_violations"' in result.output  # JSON format


def test_cli_override_config_with_options(tmp_path):
    """Test CLI options override configuration file."""
    # Create config file with fail_on_error=true
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.proboscis]
output_format = "json"
fail_on_error = true
""")
    
    # Create source without tests
    src_file = tmp_path / "module.py"
    src_file.write_text("""
def untested_function():
    pass
""")
    
    runner = CliRunner()
    # Override format to text (config says json)
    result = runner.invoke(cli, [str(tmp_path), "--format", "text"])
    
    assert result.exit_code == 1  # Still fails due to config fail_on_error=true
    assert "ERROR:" in result.output  # Text format, not JSON
    assert '"total_violations"' not in result.output


def test_cli_invalid_path():
    """Test CLI with invalid path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["/non/existent/path"])
    
    assert result.exit_code == 2  # Click exit code for invalid path


def test_cli_file_path(tmp_path):
    """Test linting a single file instead of directory."""
    # Create a single Python file
    src_file = tmp_path / "single_module.py"
    src_file.write_text("""
def single_function():
    pass
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(src_file)])
    
    assert result.exit_code == 0
    assert "single_function" in result.output


def test_cli_empty_directory(tmp_path):
    """Test linting an empty directory."""
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path)])
    
    assert result.exit_code == 0
    assert "No violations found" in result.output


def test_cli_no_python_files(tmp_path):
    """Test directory with no Python files."""
    # Create only non-Python files
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("Not a Python file")
    
    js_file = tmp_path / "script.js"
    js_file.write_text("console.log('Not Python');")
    
    runner = CliRunner()
    result = runner.invoke(cli, [str(tmp_path)])
    
    assert result.exit_code == 0
    assert "No violations found" in result.output