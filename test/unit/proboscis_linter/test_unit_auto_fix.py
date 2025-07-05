"""Unit tests for auto-fix functionality."""
import pytest
from pathlib import Path
from textwrap import dedent
from proboscis_linter.auto_fix import AutoFixer
from proboscis_linter.models import LintViolation


class TestAutoFixer:
    """Test suite for AutoFixer class."""
    
    @pytest.mark.unit
    def test_apply_add_decorator_simple(self, tmp_path):
        """Test adding a decorator to a simple function."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text(dedent('''
            @pytest.mark.unit
            def test_function():
                pass
        ''').strip())
        
        # Create a violation with fix info
        violation = LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=test_file,
            line_number=1,
            function_name="test_function",
            message="Test function needs marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=1
        )
        
        # Apply the fix
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes([violation])
        
        # Check the fix was applied
        assert str(test_file) in fixes_applied
        assert fixes_applied[str(test_file)] == 1
        
        # Check the file content
        expected = dedent('''
            @pytest.mark.unit
            def test_function():
                pass
        ''').strip()
        assert test_file.read_text() == expected
    
    @pytest.mark.unit
    def test_apply_add_decorator_with_existing_decorators(self, tmp_path):
        """Test adding a decorator when other decorators exist."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text(dedent('''
            @pytest.mark.unit
            @pytest.fixture
            def test_function():
                pass
        ''').strip())
        
        # Create a violation with fix info
        violation = LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=test_file,
            line_number=2,  # Function is on line 2
            function_name="test_function",
            message="Test function needs marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=1  # Insert before existing decorator
        )
        
        # Apply the fix
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes([violation])
        
        # Check the fix was applied
        assert str(test_file) in fixes_applied
        assert fixes_applied[str(test_file)] == 1
        
        # Check the file content
        expected = dedent('''
            @pytest.mark.unit
            @pytest.fixture
            def test_function():
                pass
        ''').strip()
        assert test_file.read_text() == expected
    
    @pytest.mark.unit
    def test_apply_add_decorator_with_indentation(self, tmp_path):
        """Test adding a decorator to an indented function."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text(dedent('''
            class TestClass:
                @pytest.mark.unit
                def test_method(self):
                    pass
        ''').strip())
        
        # Create a violation with fix info
        violation = LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=test_file,
            line_number=2,
            function_name="test_method",
            message="Test method needs marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=2
        )
        
        # Apply the fix
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes([violation])
        
        # Check the fix was applied
        assert str(test_file) in fixes_applied
        assert fixes_applied[str(test_file)] == 1
        
        # Check the file content
        expected = dedent('''
            class TestClass:
                @pytest.mark.unit
                def test_method(self):
                    pass
        ''').strip()
        assert test_file.read_text() == expected
    
    @pytest.mark.unit
    def test_apply_multiple_fixes_same_file(self, tmp_path):
        """Test applying multiple fixes to the same file."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text(dedent('''
            @pytest.mark.unit
            def test_first():
                pass
            
            @pytest.mark.unit
            def test_second():
                pass
        ''').strip())
        
        # Create violations with fix info
        violations = [
            LintViolation(
                rule_name="PL004:require-test-markers",
                file_path=test_file,
                line_number=1,
                function_name="test_first",
                message="Test function needs marker",
                severity="error",
                fix_type="add_decorator",
                fix_content="@pytest.mark.unit",
                fix_line=1
            ),
            LintViolation(
                rule_name="PL004:require-test-markers",
                file_path=test_file,
                line_number=4,
                function_name="test_second",
                message="Test function needs marker",
                severity="error",
                fix_type="add_decorator",
                fix_content="@pytest.mark.unit",
                fix_line=4
            )
        ]
        
        # Apply the fixes
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes(violations)
        
        # Check both fixes were applied
        assert str(test_file) in fixes_applied
        assert fixes_applied[str(test_file)] == 2
        
        # Check the file content
        expected = dedent('''
            @pytest.mark.unit
            def test_first():
                pass
            
            @pytest.mark.unit
            def test_second():
                pass
        ''').strip()
        assert test_file.read_text() == expected
    
    @pytest.mark.unit
    def test_skip_violations_without_fix_info(self, tmp_path):
        """Test that violations without fix info are skipped."""
        # Create a test file
        test_file = tmp_path / "test.py"
        original_content = dedent('''
            @pytest.mark.unit
            def test_function():
                pass
        ''').strip()
        test_file.write_text(original_content)
        
        # Create a violation without fix info
        violation = LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=test_file,
            line_number=1,
            function_name="test_function",
            message="Function needs test",
            severity="error"
            # No fix_type, fix_content, or fix_line
        )
        
        # Apply the fix
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes([violation])
        
        # Check no fixes were applied
        assert len(fixes_applied) == 0
        
        # Check the file content is unchanged
        assert test_file.read_text() == original_content
    
    @pytest.mark.unit
    def test_handle_file_error_gracefully(self, tmp_path):
        """Test that file errors are handled gracefully."""
        # Create a violation for a non-existent file
        violation = LintViolation(
            rule_name="PL004:require-test-markers",
            file_path=tmp_path / "non_existent.py",
            line_number=1,
            function_name="test_function",
            message="Test function needs marker",
            severity="error",
            fix_type="add_decorator",
            fix_content="@pytest.mark.unit",
            fix_line=1
        )
        
        # Apply the fix - should not raise exception
        fixer = AutoFixer()
        fixes_applied = fixer.apply_fixes([violation])
        
        # Check no fixes were applied
        assert len(fixes_applied) == 0


@pytest.mark.unit
def test_AutoFixer_apply_fixes(tmp_path):
    """Test the apply_fixes method of AutoFixer class."""
    # Create a test file
    test_file = tmp_path / "test.py"
    test_file.write_text(dedent('''
        @pytest.mark.unit
        def test_missing_marker():
            pass
    ''').strip())
    
    # Create a violation with fix info
    violation = LintViolation(
        rule_name="PL004:require-test-markers",
        file_path=test_file,
        line_number=1,
        function_name="test_missing_marker",
        message="Test function needs marker",
        severity="error",
        fix_type="add_decorator",
        fix_content="@pytest.mark.unit",
        fix_line=1
    )
    
    # Apply the fix
    fixer = AutoFixer()
    fixes_applied = fixer.apply_fixes([violation])
    
    # Check the fix was applied
    assert str(test_file) in fixes_applied
    assert fixes_applied[str(test_file)] == 1
    
    # Check the file content
    expected = dedent('''
        @pytest.mark.unit
        def test_missing_marker():
            pass
    ''').strip()
    assert test_file.read_text() == expected