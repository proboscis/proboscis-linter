"""Unit tests for the debug_files module."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import debug_files


class TestMain:
    """Test cases for main function."""

    @pytest.mark.unit
    @patch('debug_files.RustLinterWrapper')
    @patch('debug_files.ProboscisLinter')
    @patch('debug_files.ProboscisConfig')
    @patch('builtins.print')
    def test_main_basic_functionality(self, mock_print, mock_config, mock_linter_class, mock_rust_class):
        """Test basic functionality of main function."""
        # Arrange
        mock_config.return_value = Mock()
        
        # Mock Python linter
        mock_python_linter = Mock()
        mock_python_files = [
            Path("test1.py"),
            Path("test2.py"),
            Path("src/module.py")
        ]
        mock_python_linter._find_python_files.return_value = mock_python_files
        mock_linter_class.return_value = mock_python_linter
        
        # Mock Rust linter
        mock_rust_linter = Mock()
        mock_violations = [
            Mock(file_path="test1.py"),
            Mock(file_path="test2.py"),
            Mock(file_path="src/module.py")
        ]
        mock_rust_linter.lint_project.return_value = mock_violations
        mock_rust_class.return_value = mock_rust_linter
        
        # Act
        debug_files.main()
        
        # Assert
        mock_config.assert_called_once()
        mock_linter_class.assert_called_once_with(mock_config.return_value)
        mock_rust_class.assert_called_once_with(mock_config.return_value)
        mock_python_linter._find_python_files.assert_called_once_with(Path("."))
        mock_rust_linter.lint_project.assert_called_once_with(Path("."))
        
        # Verify print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Python implementation found files:" in call for call in print_calls)
        assert any("Total: 3 files" in call for call in print_calls)
        assert any("Running Rust implementation" in call for call in print_calls)

    @pytest.mark.unit
    @patch('debug_files.RustLinterWrapper')
    @patch('debug_files.ProboscisLinter')
    @patch('debug_files.ProboscisConfig')
    @patch('builtins.print')
    def test_main_with_differences(self, mock_print, mock_config, mock_linter_class, mock_rust_class):
        """Test main function when Python finds files that Rust doesn't."""
        # Arrange
        mock_config.return_value = Mock()
        
        # Mock Python linter finding more files
        mock_python_linter = Mock()
        mock_python_files = [
            Path("test1.py"),
            Path("test2.py"),
            Path("src/module.py"),
            Path("extra_file.py")
        ]
        mock_python_linter._find_python_files.return_value = mock_python_files
        mock_linter_class.return_value = mock_python_linter
        
        # Mock Rust linter finding fewer files
        mock_rust_linter = Mock()
        mock_violations = [
            Mock(file_path="test1.py"),
            Mock(file_path="test2.py"),
            Mock(file_path="src/module.py")
        ]
        mock_rust_linter.lint_project.return_value = mock_violations
        mock_rust_class.return_value = mock_rust_linter
        
        # Act
        debug_files.main()
        
        # Assert
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Files only processed by Python (1):" in call for call in print_calls)
        assert any("extra_file.py" in call for call in print_calls)

    @pytest.mark.unit
    @patch('debug_files.RustLinterWrapper')
    @patch('debug_files.ProboscisLinter')
    @patch('debug_files.ProboscisConfig')
    @patch('builtins.print')
    def test_main_no_violations(self, mock_print, mock_config, mock_linter_class, mock_rust_class):
        """Test main function when Rust finds no violations."""
        # Arrange
        mock_config.return_value = Mock()
        
        # Mock Python linter
        mock_python_linter = Mock()
        mock_python_files = [Path("test1.py"), Path("test2.py")]
        mock_python_linter._find_python_files.return_value = mock_python_files
        mock_linter_class.return_value = mock_python_linter
        
        # Mock Rust linter with no violations
        mock_rust_linter = Mock()
        mock_rust_linter.lint_project.return_value = []
        mock_rust_class.return_value = mock_rust_linter
        
        # Act
        debug_files.main()
        
        # Assert
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Rust found violations in 0 files" in call for call in print_calls)
        assert any("Files only processed by Python (2):" in call for call in print_calls)

    @pytest.mark.unit
    @patch('debug_files.RustLinterWrapper')
    @patch('debug_files.ProboscisLinter')
    @patch('debug_files.ProboscisConfig')
    @patch('builtins.print')
    def test_main_duplicate_file_paths_in_violations(self, mock_print, mock_config, mock_linter_class, mock_rust_class):
        """Test main function handles duplicate file paths in violations correctly."""
        # Arrange
        mock_config.return_value = Mock()
        
        # Mock Python linter
        mock_python_linter = Mock()
        mock_python_files = [Path("test.py")]
        mock_python_linter._find_python_files.return_value = mock_python_files
        mock_linter_class.return_value = mock_python_linter
        
        # Mock Rust linter with multiple violations in same file
        mock_rust_linter = Mock()
        mock_violations = [
            Mock(file_path="test.py"),
            Mock(file_path="test.py"),
            Mock(file_path="test.py")
        ]
        mock_rust_linter.lint_project.return_value = mock_violations
        mock_rust_class.return_value = mock_rust_linter
        
        # Act
        debug_files.main()
        
        # Assert
        print_calls = [str(call) for call in mock_print.call_args_list]
        # Should only count unique files
        assert any("Rust found violations in 1 files" in call for call in print_calls)

    @pytest.mark.unit
    @patch('debug_files.RustLinterWrapper')
    @patch('debug_files.ProboscisLinter')
    @patch('debug_files.ProboscisConfig')
    @patch('builtins.print')
    def test_main_sorted_output(self, mock_print, mock_config, mock_linter_class, mock_rust_class):
        """Test that file listings are sorted."""
        # Arrange
        mock_config.return_value = Mock()
        
        # Mock Python linter with unsorted files
        mock_python_linter = Mock()
        mock_python_files = [
            Path("z_file.py"),
            Path("a_file.py"),
            Path("m_file.py")
        ]
        mock_python_linter._find_python_files.return_value = mock_python_files
        mock_linter_class.return_value = mock_python_linter
        
        # Mock Rust linter
        mock_rust_linter = Mock()
        mock_rust_linter.lint_project.return_value = []
        mock_rust_class.return_value = mock_rust_linter
        
        # Act
        debug_files.main()
        
        # Assert
        print_calls = mock_print.call_args_list
        
        # Find the calls that print the files
        file_prints = []
        capture = False
        for call in print_calls:
            call_str = str(call)
            if "Python implementation found files:" in call_str:
                capture = True
                continue
            if capture and "Total:" in call_str:
                break
            if capture and "  " in call_str:
                file_prints.append(call_str)
        
        # Extract file names and verify they're sorted
        files = []
        for fp in file_prints:
            # Extract filename from print call
            if "a_file.py" in fp:
                files.append("a_file.py")
            elif "m_file.py" in fp:
                files.append("m_file.py")
            elif "z_file.py" in fp:
                files.append("z_file.py")
        
        assert files == ["a_file.py", "m_file.py", "z_file.py"]


if __name__ == "__main__":
    pytest.main([__file__])