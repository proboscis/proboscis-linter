"""Integration tests for auto-fix functionality."""
import pytest
from pathlib import Path
from textwrap import dedent
from proboscis_linter.auto_fix import AutoFixer
from proboscis_linter.models import LintViolation


@pytest.mark.integration
def test_AutoFixer_apply_fixes(tmp_path):
    """Integration test for the apply_fixes method of AutoFixer class."""
    # Create a test project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    test_dir = tmp_path / "test" / "unit"
    test_dir.mkdir(parents=True)
    
    # Create a test file with multiple issues
    test_file = test_dir / "test_sample.py"
    test_file.write_text(dedent('''
        @pytest.mark.integration
        def test_function_one():
            """Test without marker."""
            assert True
        
        @pytest.mark.integration
        def test_function_two():
            """Another test without marker."""
            assert 1 + 1 == 2
        
        @pytest.mark.integration
        @pytest.mark.unit
        def test_function_three():
            """Test with marker."""
            pass
    ''').strip())
    
    # Create violations for missing markers
    violations = [
        LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=test_file,
            line_number=1,
            function_name="test_function_one",
            message="Test function 'test_function_one' is missing a pytest marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=1
        ),
        LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=test_file,
            line_number=5,
            function_name="test_function_two",
            message="Test function 'test_function_two' is missing a pytest marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=5
        )
    ]
    
    # Apply fixes
    fixer = AutoFixer()
    fixes_applied = fixer.apply_fixes(violations)
    
    # Verify fixes were applied
    assert str(test_file) in fixes_applied
    assert fixes_applied[str(test_file)] == 2
    
    # Verify the file content
    expected = dedent('''
        @pytest.mark.unit
        @pytest.mark.integration
        def test_function_one():
            """Test without marker."""
            assert True
        @pytest.mark.unit
        
        @pytest.mark.integration
        def test_function_two():
            """Another test without marker."""
            assert 1 + 1 == 2
        
        @pytest.mark.integration
        @pytest.mark.unit
        def test_function_three():
            """Test with marker."""
            pass
    ''').strip()
    assert test_file.read_text() == expected