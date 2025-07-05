"""Unit tests for the benchmark module."""
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from proboscis_linter.models import LintViolation


# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import benchmark


@pytest.mark.unit
def test_benchmark_implementation():
    """Test the benchmark_implementation function."""
    # Arrange
    mock_linter = Mock()
    mock_violations = [
        LintViolation(
            rule_name="TEST001",
            file_path=Path("test.py"),
            line_number=1,
            function_name="test_function",
            message="Test violation",
            severity="error"
        )
    ]
    mock_linter.lint_project.return_value = mock_violations
    project_path = Path("/test/project")

    # Act
    with patch('builtins.print'):
        duration, violation_count = benchmark.benchmark_implementation(
            mock_linter, project_path, "Test"
        )

    # Assert
    assert isinstance(duration, float)
    assert duration > 0
    assert violation_count == 1
    mock_linter.lint_project.assert_called_once_with(project_path)


class TestBenchmarkImplementation:
    """Test cases for benchmark_implementation function."""

    @pytest.mark.unit
    def test_benchmark_implementation_success(self):
        """Test successful benchmarking of a linter implementation."""
        # Arrange
        mock_linter = Mock()
        mock_violations = [
            LintViolation(
                rule_name="TEST001",
                file_path=Path("test.py"),
                line_number=1,
                function_name="test_function",
                message="Test violation",
                severity="error"
            ),
            LintViolation(
                rule_name="TEST002",
                file_path=Path("test2.py"),
                line_number=2,
                function_name="test_another_function",
                message="Another test violation",
                severity="warning"
            )
        ]
        mock_linter.lint_project.return_value = mock_violations
        project_path = Path("/test/project")

        # Act
        with patch('builtins.print'):
            duration, violation_count = benchmark.benchmark_implementation(
                mock_linter, project_path, "Test"
            )

        # Assert
        assert isinstance(duration, float)
        assert duration > 0
        assert violation_count == 2
        mock_linter.lint_project.assert_called_once_with(project_path)

    @pytest.mark.unit
    def test_benchmark_implementation_no_violations(self):
        """Test benchmarking when no violations are found."""
        # Arrange
        mock_linter = Mock()
        mock_linter.lint_project.return_value = []
        project_path = Path("/test/project")

        # Act
        with patch('builtins.print'):
            duration, violation_count = benchmark.benchmark_implementation(
                mock_linter, project_path, "Test"
            )

        # Assert
        assert isinstance(duration, float)
        assert duration > 0
        assert violation_count == 0
        mock_linter.lint_project.assert_called_once_with(project_path)

    @pytest.mark.unit
    def test_benchmark_implementation_prints_results(self):
        """Test that benchmark results are printed correctly."""
        # Arrange
        mock_linter = Mock()
        mock_linter.lint_project.return_value = [Mock(), Mock(), Mock()]
        project_path = Path("/test/project")
        
        # Act
        with patch('builtins.print') as mock_print:
            duration, violation_count = benchmark.benchmark_implementation(
                mock_linter, project_path, "TestLinter"
            )

        # Assert
        calls = mock_print.call_args_list
        assert any("TestLinter Implementation:" in str(call) for call in calls)
        assert any("Time:" in str(call) and "seconds" in str(call) for call in calls)
        assert any("Violations found: 3" in str(call) for call in calls)

    @pytest.mark.unit
    def test_benchmark_implementation_timing_accuracy(self):
        """Test that timing measurement is accurate."""
        # Arrange
        mock_linter = Mock()
        
        # Make lint_project take some time
        def slow_lint(path):
            time.sleep(0.1)
            return []
        
        mock_linter.lint_project.side_effect = slow_lint
        project_path = Path("/test/project")

        # Act
        with patch('builtins.print'):
            duration, _ = benchmark.benchmark_implementation(
                mock_linter, project_path, "Test"
            )

        # Assert
        assert duration >= 0.1  # Should be at least 0.1 seconds
        assert duration < 0.2  # But not too much more


class TestMain:
    """Test cases for main function."""

    @pytest.mark.unit
    def test_main_no_arguments(self):
        """Test main function with no command line arguments."""
        # Arrange
        with patch.object(sys, 'argv', ['benchmark.py']):
            
            # Act & Assert
            with pytest.raises(SystemExit) as exc_info:
                with patch('builtins.print') as mock_print:
                    benchmark.main()
            
            assert exc_info.value.code == 1
            mock_print.assert_called_with("Usage: python benchmark.py <project_path>")

    @pytest.mark.unit
    def test_main_nonexistent_path(self):
        """Test main function with a non-existent project path."""
        # Arrange
        nonexistent_path = "/this/path/does/not/exist"
        with patch.object(sys, 'argv', ['benchmark.py', nonexistent_path]):
            
            # Act & Assert
            with pytest.raises(SystemExit) as exc_info:
                with patch('builtins.print') as mock_print:
                    benchmark.main()
            
            assert exc_info.value.code == 1
            mock_print.assert_called_with(f"Error: {nonexistent_path} does not exist")

    @pytest.mark.unit
    @patch('benchmark.ProboscisConfig')
    @patch('benchmark.ProboscisLinter')
    @patch('benchmark.RustLinterWrapper')
    @patch('benchmark.benchmark_implementation')
    @patch('pathlib.Path.exists')
    def test_main_successful_benchmark(self, mock_exists, mock_benchmark, 
                                     mock_rust_wrapper, mock_linter, mock_config):
        """Test successful benchmarking of both implementations."""
        # Arrange
        mock_exists.return_value = True
        mock_config.return_value = Mock()
        mock_linter.return_value = Mock()
        mock_rust_wrapper.return_value = Mock()
        
        # Mock benchmark results
        mock_benchmark.side_effect = [
            (2.5, 100),  # Python implementation
            (0.5, 100),  # Rust implementation
        ]
        
        with patch.object(sys, 'argv', ['benchmark.py', '/test/project']):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                # Check that both implementations were benchmarked
                assert mock_benchmark.call_count == 2
                
                # Check speedup calculation was printed
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Rust is 5.00x faster than Python" in call for call in calls)

    @pytest.mark.unit
    @patch('benchmark.ProboscisConfig')
    @patch('benchmark.ProboscisLinter')
    @patch('benchmark.RustLinterWrapper')
    @patch('benchmark.benchmark_implementation')
    @patch('pathlib.Path.exists')
    def test_main_different_violation_counts(self, mock_exists, mock_benchmark,
                                           mock_rust_wrapper, mock_linter, mock_config):
        """Test warning when implementations find different violation counts."""
        # Arrange
        mock_exists.return_value = True
        mock_config.return_value = Mock()
        mock_linter.return_value = Mock()
        mock_rust_wrapper.return_value = Mock()
        
        # Mock different violation counts
        mock_benchmark.side_effect = [
            (2.5, 100),  # Python implementation
            (0.5, 95),   # Rust implementation (different count)
        ]
        
        with patch.object(sys, 'argv', ['benchmark.py', '/test/project']):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("WARNING: Different violation counts!" in call for call in calls)
                assert any("Python: 100" in call for call in calls)
                assert any("Rust: 95" in call for call in calls)

    @pytest.mark.unit
    @patch('benchmark.ProboscisConfig')
    @patch('benchmark.ProboscisLinter')
    @patch('benchmark.RustLinterWrapper')
    @patch('benchmark.benchmark_implementation')
    @patch('pathlib.Path.exists')
    def test_main_rust_import_error(self, mock_exists, mock_benchmark,
                                  mock_rust_wrapper, mock_linter, mock_config):
        """Test handling of Rust implementation import error."""
        # Arrange
        mock_exists.return_value = True
        mock_config.return_value = Mock()
        mock_linter.return_value = Mock()
        
        # Mock Rust import failure
        mock_rust_wrapper.side_effect = ImportError("Rust extension not found")
        
        # Mock Python benchmark result
        mock_benchmark.return_value = (2.5, 100)
        
        with patch.object(sys, 'argv', ['benchmark.py', '/test/project']):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                # Should benchmark Python only
                assert mock_benchmark.call_count == 1
                
                # Check error message
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Rust implementation not available" in call for call in calls)
                assert any("Run 'maturin develop'" in call for call in calls)

    @pytest.mark.unit
    @patch('benchmark.ProboscisConfig')
    @patch('benchmark.ProboscisLinter')
    @patch('benchmark.RustLinterWrapper')
    @patch('benchmark.benchmark_implementation')
    @patch('pathlib.Path.exists')
    def test_main_zero_rust_time(self, mock_exists, mock_benchmark,
                                mock_rust_wrapper, mock_linter, mock_config):
        """Test handling of zero execution time for Rust implementation."""
        # Arrange
        mock_exists.return_value = True
        mock_config.return_value = Mock()
        mock_linter.return_value = Mock()
        mock_rust_wrapper.return_value = Mock()
        
        # Mock benchmark results with zero Rust time
        mock_benchmark.side_effect = [
            (2.5, 100),  # Python implementation
            (0.0, 100),  # Rust implementation (zero time)
        ]
        
        with patch.object(sys, 'argv', ['benchmark.py', '/test/project']):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                calls = [str(call) for call in mock_print.call_args_list]
                # Should handle division by zero gracefully
                assert any("Rust is inf" in call or "Rust is" in call for call in calls)


if __name__ == "__main__":
    pytest.main([__file__])