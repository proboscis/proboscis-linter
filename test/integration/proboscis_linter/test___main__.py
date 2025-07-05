"""Integration tests for __main__ module."""
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from proboscis_linter.__main__ import main


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
def test_tested_function():
    pass
""")
            
            yield root
    
    def test_main_with_cli_integration(self, sample_project):
        """Test main() integrates properly with CLI."""
        with patch('sys.argv', ['proboscis-linter', str(sample_project)]):
            runner = CliRunner()
            
            # Capture the output by patching click.echo
            outputs = []
            with patch('click.echo', side_effect=lambda x: outputs.append(x)):
                try:
                    main()
                except SystemExit as e:
                    # CLI might exit with 0 or 1 depending on violations
                    assert e.code in [0, 1]
            
            # Check that output was generated
            output_text = '\n'.join(outputs)
            assert "untested_function" in output_text
            assert "violations" in output_text.lower()
    
    def test_main_command_line_options(self, sample_project):
        """Test main() with various command line options."""
        test_cases = [
            # (args, expected_in_output)
            (['--help'], ['proboscis-lint', 'Usage:']),
            (['--version'], ['version']),
            ([str(sample_project), '--format', 'json'], ['"total_violations"']),
            ([str(sample_project), '--format', 'text'], ['ERROR:', 'untested_function']),
            ([str(sample_project), '--verbose'], ['DEBUG', 'Linting']),
        ]
        
        for args, expected_strings in test_cases:
            with patch('sys.argv', ['proboscis-linter'] + args):
                runner = CliRunner()
                
                # Use CliRunner to capture output properly
                result = runner.invoke(main, catch_exceptions=False)
                
                # Help and version cause early exit
                if '--help' in args or '--version' in args:
                    assert result.exit_code == 0
                
                # Check expected strings in output
                for expected in expected_strings:
                    assert expected in result.output or expected.lower() in result.output.lower()
    
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
        
        with patch('sys.argv', ['proboscis-linter', str(sample_project)]):
            runner = CliRunner()
            result = runner.invoke(main, catch_exceptions=False)
            
            # Should fail due to fail_on_error=true
            assert result.exit_code == 1
            
            # Should use JSON format from config
            assert '"total_violations"' in result.output
            assert '"violations"' in result.output
    
    def test_main_error_handling(self):
        """Test main() handles various error conditions."""
        # Test with non-existent path
        with patch('sys.argv', ['proboscis-linter', '/non/existent/path']):
            runner = CliRunner()
            result = runner.invoke(main)
            assert result.exit_code == 2  # Click error code for invalid path
        
        # Test with invalid option
        with patch('sys.argv', ['proboscis-linter', '--invalid-option']):
            runner = CliRunner()
            result = runner.invoke(main)
            assert result.exit_code == 2
            assert "Error" in result.output or "error" in result.output
    
    def test_main_subprocess_execution(self, sample_project):
        """Test executing __main__ as a subprocess."""
        # Test running as module
        result = subprocess.run(
            [sys.executable, '-m', 'proboscis_linter', str(sample_project), '--format', 'json'],
            capture_output=True,
            text=True,
            cwd=str(sample_project.parent)
        )
        
        # Should complete successfully
        assert result.returncode in [0, 1]  # 0 if no violations, 1 if violations with fail_on_error
        assert '"total_violations"' in result.stdout
        
        # Test running __main__.py directly
        main_file = Path(__file__).parent.parent.parent / "src" / "proboscis_linter" / "__main__.py"
        if main_file.exists():
            result = subprocess.run(
                [sys.executable, str(main_file), str(sample_project)],
                capture_output=True,
                text=True
            )
            assert result.returncode in [0, 1]
            assert "violations" in result.stdout.lower()
    
    def test_main_with_multiple_files(self):
        """Test main() with multiple source files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create multiple modules
            for i in range(3):
                module = root / f"module{i}.py"
                module.write_text(f"""
def function_{i}_a():
    pass

def function_{i}_b():
    pass
""")
            
            with patch('sys.argv', ['proboscis-linter', str(root)]):
                runner = CliRunner()
                result = runner.invoke(main, catch_exceptions=False)
                
                # Should find violations for all functions
                assert result.exit_code == 0
                for i in range(3):
                    assert f"function_{i}_a" in result.output
                    assert f"function_{i}_b" in result.output
    
    def test_main_changed_only_integration(self, sample_project):
        """Test main() with --changed-only option."""
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=sample_project, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                      cwd=sample_project, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                      cwd=sample_project, capture_output=True)
        
        # Initial commit
        subprocess.run(['git', 'add', '.'], cwd=sample_project, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                      cwd=sample_project, capture_output=True)
        
        # Add a new file
        new_file = sample_project / "src" / "new_module.py"
        new_file.write_text("""
def new_function():
    pass
""")
        
        with patch('sys.argv', ['proboscis-linter', str(sample_project), '--changed-only']):
            runner = CliRunner()
            result = runner.invoke(main, catch_exceptions=False)
            
            # Should only report violations for the new file
            assert "new_function" in result.output
    
    def test_main_exit_codes(self, sample_project):
        """Test main() returns correct exit codes."""
        # Test success case (no violations)
        clean_project = sample_project.parent / "clean"
        clean_project.mkdir()
        (clean_project / "module.py").write_text("""
def tested():  # noqa: PL001, PL002, PL003
    pass
""")
        
        with patch('sys.argv', ['proboscis-linter', str(clean_project)]):
            runner = CliRunner()
            result = runner.invoke(main, catch_exceptions=False)
            assert result.exit_code == 0
            assert "No violations found" in result.output
        
        # Test failure case with --fail-on-error
        with patch('sys.argv', ['proboscis-linter', str(sample_project), '--fail-on-error']):
            runner = CliRunner()
            result = runner.invoke(main, catch_exceptions=False)
            assert result.exit_code == 1