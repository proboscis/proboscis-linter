"""Integration tests for __main__ module."""
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from proboscis_linter.__main__ import main
from proboscis_linter.cli import cli


class TestMainIntegration:
    """Integration tests for __main__ module."""
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create source file
            src = root / "src"
            src.mkdir()
            (src / "module.py").write_text("""
def tested_function():
    pass

def untested_function():
    pass
""")
            
            # Create test file
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_module.py").write_text("""
@pytest.mark.integration
def test_tested_function():
    pass
""")
            
            yield root
    
    @pytest.mark.integration
    def test_main_with_cli_integration(self, sample_project):
        """Test main() integrates properly with CLI."""
        with patch('sys.argv', ['proboscis-linter', str(sample_project)]):
            runner = CliRunner()
            
            # Capture the output by patching click.echo
            outputs = []
            with patch('click.echo', side_effect=lambda x: outputs.append(x)):
                try:
                    main()
                except SystemExit:
                    pass
            
            # Check that output was generated
            output_text = ' '.join(str(o) for o in outputs)
            assert "violations" in output_text.lower()
    
    @pytest.mark.integration
    def test_main_command_line_options(self, sample_project):
        """Test main() with various command line options."""
        test_cases = [
            # (args, expected_in_output)
            (['--help'], ['Usage:', 'Options:']),
            (['--version'], ['version']),
            ([str(sample_project), '--format', 'json'], ['"total_violations"']),
            ([str(sample_project), '--format', 'text'], ['violations']),
            ([str(sample_project), '--verbose'], ['INFO']),
        ]
        
        runner = CliRunner()
        for args, expected_strings in test_cases:
            # Use CliRunner to capture output properly
            result = runner.invoke(cli, args, catch_exceptions=False)
            
            # Help and version cause early exit
            if '--help' in args or '--version' in args:
                assert result.exit_code == 0
            
            # Check expected strings in output
            for expected in expected_strings:
                assert expected in result.output or expected.lower() in result.output.lower()
    
    @pytest.mark.integration
    def test_main_with_config_file(self, sample_project):
        """Test main() respects configuration file."""
        # Create config file
        config_file = sample_project / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = false
PL003 = false
""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [str(sample_project)])
        
        # Should output JSON format as per config
        assert '"total_violations"' in result.output
        
        # Should fail with non-zero exit due to fail_on_error
        assert result.exit_code == 1
    
    @pytest.mark.integration
    def test_main_error_handling(self):
        """Test main() handles errors gracefully."""
        runner = CliRunner()
        
        # Test with non-existent path
        nonexistent = Path("/this/does/not/exist")
        result = runner.invoke(cli, [str(nonexistent)])
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output
    
    @pytest.mark.integration
    def test_main_subprocess_execution(self, sample_project):
        """Test main can be executed as subprocess."""
        # Run as subprocess
        result = subprocess.run(
            [sys.executable, "-m", "proboscis_linter", str(sample_project)],
            capture_output=True,
            text=True
        )
        
        # Should complete successfully
        assert "violations" in result.stdout.lower() or "violations" in result.stderr.lower()
    
    @pytest.mark.integration
    def test_main_with_multiple_files(self, sample_project):
        """Test main() handles multiple files."""
        # Create additional source file
        src = sample_project / "src"
        (src / "another.py").write_text("""
def another_untested():
    pass
""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [str(sample_project)], catch_exceptions=False)
        
        # Should find violations in both files
        assert "module.py" in result.output
        assert "another.py" in result.output
    
    @pytest.mark.integration
    def test_main_changed_only_integration(self, sample_project):
        """Test main() with --changed-only flag."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=sample_project, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=sample_project, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=sample_project, check=True)
        
        # Add and commit initial files
        subprocess.run(["git", "add", "."], cwd=sample_project, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=sample_project, check=True)
        
        # Create new file
        (sample_project / "src" / "new.py").write_text("""
def new_untested():
    pass
""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [str(sample_project), '--changed-only'], catch_exceptions=False)
        
        # Should only check the new file
        assert "new.py" in result.output
        assert "module.py" not in result.output
    
    @pytest.mark.integration
    def test_main_exit_codes(self, sample_project):
        """Test main() returns correct exit codes."""
        # Test success case (no violations)
        clean_project = sample_project.parent / "clean"
        clean_project.mkdir(exist_ok=True)
        (clean_project / "module.py").write_text("""
def tested():  # noqa: PL001, PL002, PL003
    pass
""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [str(clean_project)], catch_exceptions=False)
        assert result.exit_code == 0
        
        # Test failure case (violations exist)
        runner = CliRunner()
        result = runner.invoke(cli, [str(sample_project), '--fail-on-error'])
        assert result.exit_code != 0