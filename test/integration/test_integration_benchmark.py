"""Integration tests for the benchmark module."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from proboscis_linter.config import ProboscisConfig
from proboscis_linter.models import LintViolation


# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import benchmark


@pytest.mark.integration
def test_benchmark_implementation():
    """Integration test for the benchmark_implementation function."""
    # Arrange
    mock_linter = Mock()
    violations = [
        LintViolation(
            rule_name="PROB001",
            file_path=Path("test.py"),
            line_number=1,
            function_name="test_function",
            message="Test violation",
            severity="error"
        )
    ]
    mock_linter.lint_project.return_value = violations
    project_path = Path("/test/project")

    # Act
    with patch('builtins.print'):
        duration, violation_count = benchmark.benchmark_implementation(
            mock_linter, project_path, "Integration"
        )

    # Assert
    assert isinstance(duration, float)
    assert duration > 0
    assert violation_count == 1
    mock_linter.lint_project.assert_called_once_with(project_path)


class TestBenchmarkImplementation:
    """Integration tests for benchmark_implementation function."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create test directory structure
            test_dir = project_path / "test"
            test_dir.mkdir()
            
            # Create a test file with violations
            test_file = test_dir / "test_example.py"
            test_file.write_text("""
import pytest

@pytest.mark.integration
def test_missing_implementation():
    '''Test with no implementation.'''
    pass

@pytest.mark.integration
def test_another_missing():
    pass
""")
            
            # Create another test file
            test_file2 = test_dir / "test_another.py"
            test_file2.write_text("""
@pytest.mark.integration
def test_valid():
    assert True

@pytest.mark.integration
def test_also_valid():
    assert 1 + 1 == 2
""")
            
            yield project_path

    @pytest.mark.integration
    def test_benchmark_implementation_with_real_config(self, temp_project):
        """Test benchmarking with real configuration object."""
        # Arrange
        ProboscisConfig()  # Ensure it can be created
        mock_linter = Mock()
        
        # Simulate realistic violations
        violations = [
            LintViolation(
                rule_name="PROB001",
                file_path=temp_project / "test/test_example.py",
                line_number=4,
                function_name="test_missing_implementation",
                message="Test function has no implementation",
                severity="error"
            ),
            LintViolation(
                rule_name="PROB001",
                file_path=temp_project / "test/test_example.py",
                line_number=8,
                function_name="test_another_missing",
                message="Test function has no implementation",
                severity="error"
            )
        ]
        mock_linter.lint_project.return_value = violations
        
        # Act
        with patch('builtins.print') as mock_print:
            duration, violation_count = benchmark.benchmark_implementation(
                mock_linter, temp_project, "Integration Test"
            )
        
        # Assert
        assert duration > 0
        assert violation_count == 2
        mock_linter.lint_project.assert_called_once_with(temp_project)
        
        # Verify output format
        output_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Integration Test Implementation:" in call for call in output_calls)
        assert any("Violations found: 2" in call for call in output_calls)

    @pytest.mark.integration
    def test_benchmark_implementation_performance_measurement(self, temp_project):
        """Test that performance is measured accurately for different execution times."""
        # Arrange
        import time
        
        # Create two mock linters with different execution times
        fast_linter = Mock()
        slow_linter = Mock()
        
        def fast_lint(path):
            time.sleep(0.01)  # 10ms
            return []
        
        def slow_lint(path):
            time.sleep(0.1)  # 100ms
            return []
        
        fast_linter.lint_project.side_effect = fast_lint
        slow_linter.lint_project.side_effect = slow_lint
        
        # Act
        with patch('builtins.print'):
            fast_duration, _ = benchmark.benchmark_implementation(
                fast_linter, temp_project, "Fast"
            )
            slow_duration, _ = benchmark.benchmark_implementation(
                slow_linter, temp_project, "Slow"
            )
        
        # Assert
        assert fast_duration < slow_duration
        assert fast_duration >= 0.01
        assert slow_duration >= 0.1
        # Allow some overhead
        assert fast_duration < 0.05
        assert slow_duration < 0.15


class TestMain:
    """Integration tests for main function."""

    @pytest.fixture
    def temp_project_with_config(self):
        """Create a temporary project with configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create test directory
            test_dir = project_path / "test"
            test_dir.mkdir()
            
            # Create configuration file
            config_file = project_path / "pyproject.toml"
            config_file.write_text("""
[tool.proboscis]
test_directories = ["test", "tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = ["**/conftest.py"]

[tool.proboscis.rules.PROB001]
enabled = true
""")
            
            # Create test files
            test_file = test_dir / "test_sample.py"
            test_file.write_text("""
@pytest.mark.integration
def test_empty():
    pass

@pytest.mark.integration
def test_with_implementation():
    assert True
""")
            
            yield project_path

    @pytest.mark.integration
    @patch('benchmark.RustLinterWrapper')
    def test_main_integration_with_config_loading(self, mock_rust_wrapper, temp_project_with_config):
        """Test main function with configuration loading from project."""
        # Arrange
        mock_rust_wrapper.return_value = Mock()
        
        # Mock the lint_project method to return some violations
        mock_rust_wrapper.return_value.lint_project.return_value = [
            Mock(spec=LintViolation) for _ in range(3)
        ]
        
        with patch.object(sys, 'argv', ['benchmark.py', str(temp_project_with_config)]):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                # Verify configuration was loaded
                assert mock_rust_wrapper.called
                
                # Verify benchmark was run
                output = [str(call) for call in mock_print.call_args_list]
                assert any(f"Benchmarking linter on: {temp_project_with_config}" in call for call in output)
                assert any("Python Implementation:" in call for call in output)
                assert any("Rust Implementation:" in call for call in output)
                assert any("Performance Comparison:" in call for call in output)

    @pytest.mark.integration
    @patch('benchmark.ProboscisLinter')
    @patch('benchmark.RustLinterWrapper')
    def test_main_integration_with_different_implementations(self, mock_rust_wrapper, 
                                                           mock_python_linter, temp_project_with_config):
        """Test main comparing different implementation results."""
        # Arrange
        # Mock Python linter to be slower
        python_instance = Mock()
        mock_python_linter.return_value = python_instance
        
        def slow_python_lint(path):
            import time
            time.sleep(0.05)  # 50ms
            return [Mock(spec=LintViolation) for _ in range(10)]
        
        python_instance.lint_project.side_effect = slow_python_lint
        
        # Mock Rust linter to be faster
        rust_instance = Mock()
        mock_rust_wrapper.return_value = rust_instance
        
        def fast_rust_lint(path):
            import time
            time.sleep(0.01)  # 10ms
            return [Mock(spec=LintViolation) for _ in range(10)]
        
        rust_instance.lint_project.side_effect = fast_rust_lint
        
        with patch.object(sys, 'argv', ['benchmark.py', str(temp_project_with_config)]):
            with patch('builtins.print') as mock_print:
                
                # Act
                benchmark.main()
                
                # Assert
                output = [str(call) for call in mock_print.call_args_list]
                
                # Should show Rust is faster
                speedup_line = next((call for call in output if "Rust is" in call and "faster" in call), None)
                assert speedup_line is not None
                
                # Extract speedup value
                import re
                match = re.search(r'Rust is (\d+\.\d+)x faster', speedup_line)
                assert match is not None
                speedup = float(match.group(1))
                
                # Rust should be at least 2x faster given our timing
                assert speedup >= 2.0

    @pytest.mark.integration
    @patch('benchmark.RustLinterWrapper')
    def test_main_integration_error_handling(self, mock_rust_wrapper, temp_project_with_config):
        """Test main function handles errors during benchmarking gracefully."""
        # Arrange
        # Make Rust wrapper raise ImportError
        mock_rust_wrapper.side_effect = ImportError("maturin not installed")
        
        with patch.object(sys, 'argv', ['benchmark.py', str(temp_project_with_config)]):
            with patch('builtins.print') as mock_print:
                
                # Act (should not raise exception)
                benchmark.main()
                
                # Assert
                output = [str(call) for call in mock_print.call_args_list]
                
                # Should show Python results
                assert any("Python Implementation:" in call for call in output)
                
                # Should show Rust error message
                assert any("Rust implementation not available" in call for call in output)
                assert any("maturin" in call for call in output)

    @pytest.mark.integration
    def test_main_integration_with_empty_project(self):
        """Test benchmarking an empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_project = Path(tmpdir)
            
            with patch.object(sys, 'argv', ['benchmark.py', str(empty_project)]):
                with patch('builtins.print') as mock_print:
                    with patch('benchmark.RustLinterWrapper'):
                        
                        # Act
                        benchmark.main()
                        
                        # Assert
                        output = [str(call) for call in mock_print.call_args_list]
                        
                        # Should complete without errors
                        assert any("Python Implementation:" in call for call in output)
                        assert any("Violations found: 0" in call for call in output)


if __name__ == "__main__":
    pytest.main([__file__])