"""Integration tests for auto-fix functionality."""
import pytest
from pathlib import Path
from textwrap import dedent
from click.testing import CliRunner
from proboscis_linter.cli import cli


class TestAutoFixIntegration:
    """Integration tests for auto-fix feature."""
    
    def test_fix_missing_pytest_markers(self, tmp_path):
        """Test fixing missing pytest markers with --fix flag."""
        # Create test directory structure
        test_dir = tmp_path / "test" / "unit"
        test_dir.mkdir(parents=True)
        
        # Create a test file without markers
        test_file = test_dir / "test_example.py"
        test_file.write_text(dedent('''
            def test_simple():
                assert True
            
            def test_another():
                assert 1 + 1 == 2
        ''').strip())
        
        # Run linter with --fix flag
        runner = CliRunner()
        result = runner.invoke(cli, [str(tmp_path), "--fix"])
        
        # Check the fixes were applied
        assert result.exit_code == 0
        # After fixes are applied, there should be no violations
        assert "No violations found" in result.output
        
        # Check the file content was updated
        expected = dedent('''
            @pytest.mark.unit
            def test_simple():
                assert True
            
            @pytest.mark.unit
            def test_another():
                assert 1 + 1 == 2
        ''').strip()
        assert test_file.read_text() == expected
    
    def test_fix_with_existing_decorators(self, tmp_path):
        """Test fixing when test already has other decorators."""
        # Create test directory structure
        test_dir = tmp_path / "test" / "integration"
        test_dir.mkdir(parents=True)
        
        # Create a test file with existing decorator
        test_file = test_dir / "test_example.py"
        test_file.write_text(dedent('''
            import pytest
            
            @pytest.fixture
            def setup():
                return "data"
            
            @pytest.mark.parametrize("value", [1, 2, 3])
            def test_parametrized(value):
                assert value > 0
        ''').strip())
        
        # Run linter with --fix flag
        runner = CliRunner()
        result = runner.invoke(cli, [str(tmp_path), "--fix"])
        
        # Check the fixes were applied
        assert result.exit_code == 0
        
        # Check the file content was updated correctly
        content = test_file.read_text()
        # The parametrized test should have the marker added
        assert "@pytest.mark.integration" in content
        assert content.count("@pytest.mark.parametrize") == 1
    
    def test_fix_only_fixes_enabled_rules(self, tmp_path):
        """Test that --fix only fixes violations for enabled rules."""
        # Create test directory structure
        test_dir = tmp_path / "test" / "unit"
        test_dir.mkdir(parents=True)
        
        # Create a config file that disables PL004
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(dedent('''
            [tool.proboscis]
            [tool.proboscis.rules]
            PL004 = false
        '''))
        
        # Create a test file without markers
        test_file = test_dir / "test_example.py"
        original_content = dedent('''
            def test_simple():
                assert True
        ''').strip()
        test_file.write_text(original_content)
        
        # Run linter with --fix flag
        runner = CliRunner()
        result = runner.invoke(cli, [str(tmp_path), "--fix"])
        
        # Check no fixes were applied (rule is disabled)
        assert result.exit_code == 0
        assert "Applying automatic fixes" not in result.output
        
        # Check the file content is unchanged
        assert test_file.read_text() == original_content
    
    def test_fix_with_verbose_output(self, tmp_path):
        """Test --fix with verbose output."""
        # Create test directory structure
        test_dir = tmp_path / "test" / "e2e"
        test_dir.mkdir(parents=True)
        
        # Create a test file without markers
        test_file = test_dir / "test_example.py"
        test_file.write_text(dedent('''
            def test_e2e_scenario():
                pass
        ''').strip())
        
        # Run linter with --fix and --verbose flags
        runner = CliRunner()
        result = runner.invoke(cli, [str(tmp_path), "--fix", "--verbose"])
        
        # Check verbose output
        assert result.exit_code == 0
        assert "Applying automatic fixes" in result.output
        assert "Applied 1 fixes to" in result.output
        assert "Re-linting after applying fixes" in result.output
        
        # Check the fix was applied
        content = test_file.read_text()
        assert "@pytest.mark.e2e" in content
    
    def test_fix_preserves_indentation(self, tmp_path):
        """Test that --fix preserves proper indentation."""
        # Create test directory structure
        test_dir = tmp_path / "test" / "unit"
        test_dir.mkdir(parents=True)
        
        # Create a test file with class methods
        test_file = test_dir / "test_class.py"
        test_file.write_text(dedent('''
            class TestMath:
                def test_addition(self):
                    assert 1 + 1 == 2
                
                def test_subtraction(self):
                    assert 5 - 3 == 2
        ''').strip())
        
        # Run linter with --fix flag
        runner = CliRunner()
        result = runner.invoke(cli, [str(tmp_path), "--fix"])
        
        # Check the fixes were applied
        assert result.exit_code == 0
        
        # Check indentation is preserved
        expected = dedent('''
            class TestMath:
                @pytest.mark.unit
                def test_addition(self):
                    assert 1 + 1 == 2
                
                @pytest.mark.unit
                def test_subtraction(self):
                    assert 5 - 3 == 2
        ''').strip()
        assert test_file.read_text() == expected