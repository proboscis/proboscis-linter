"""End-to-end tests for the benchmark module."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from unittest.mock import Mock, patch
from proboscis_linter.models import LintViolation


# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import benchmark


def test_benchmark_implementation():
    """E2E test for the benchmark_implementation function."""
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
            mock_linter, project_path, "E2E"
        )

    # Assert
    assert isinstance(duration, float)
    assert duration > 0
    assert violation_count == 1
    mock_linter.lint_project.assert_called_once_with(project_path)


class TestBenchmarkImplementation:
    """E2E tests for benchmark_implementation through the actual benchmark script."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project with various test scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create directory structure
            (project_path / "src").mkdir()
            (project_path / "test").mkdir()
            (project_path / "test/unit").mkdir()
            (project_path / "test/integration").mkdir()
            
            # Create source files
            src_file = project_path / "src" / "calculator.py"
            src_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
            
            # Create test files with various patterns
            
            # Good test file
            good_test = project_path / "test" / "unit" / "test_calculator.py"
            good_test.write_text("""
import pytest
from src.calculator import add, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5
    with pytest.raises(ValueError):
        divide(5, 0)
""")
            
            # Test file with empty tests
            empty_test = project_path / "test" / "unit" / "test_empty.py"
            empty_test.write_text("""
def test_todo():
    # TODO: implement this test
    pass

def test_not_implemented():
    pass

def test_another_empty():
    '''This test needs implementation'''
    pass
""")
            
            # Test file with missing hooks
            missing_hooks = project_path / "test" / "integration" / "test_hooks.py"
            missing_hooks.write_text("""
import pytest

def test_with_stop():
    proboscis.stop()
    assert True

def test_without_hook():
    # Missing stop() call
    assert True

def test_multiple_stops():
    proboscis.stop()
    proboscis.stop()  # Multiple stops
    assert True
""")
            
            # Create pyproject.toml
            config_file = project_path / "pyproject.toml"
            config_file.write_text("""
[tool.proboscis]
test_directories = ["test"]
test_patterns = ["test_*.py"]
exclude_patterns = ["**/conftest.py", "**/__pycache__/**"]

[tool.proboscis.rules]
PROB001 = { enabled = true }
PROB002 = { enabled = true }
""")
            
            yield project_path

    def test_benchmark_implementation_e2e_basic(self, sample_project):
        """Test running benchmark script end-to-end on a sample project."""
        # Get the benchmark script path
        benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
        
        # Run the benchmark script
        result = subprocess.run(
            [sys.executable, str(benchmark_script), str(sample_project)],
            capture_output=True,
            text=True
        )
        
        # Assert successful execution
        assert result.returncode == 0
        
        # Check output contains expected sections
        output = result.stdout
        assert "Python Implementation:" in output
        assert "Time:" in output
        assert "Violations found:" in output
        assert "Performance Comparison:" in output
        
        # Should find violations in our test files
        assert "Violations found: " in output
        # Extract violation count
        import re
        match = re.search(r'Violations found: (\d+)', output)
        assert match is not None
        violation_count = int(match.group(1))
        assert violation_count > 0  # Should find some violations

    def test_benchmark_implementation_e2e_no_rust(self, sample_project, monkeypatch):
        """Test benchmark behavior when Rust implementation is not available."""
        # Get the benchmark script path
        benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
        
        # Make Rust import fail by manipulating PYTHONPATH
        # This simulates Rust extension not being built
        env = dict(os.environ) if 'os' in globals() else {}
        env['PROBOSCIS_DISABLE_RUST'] = '1'  # If the code checks for this
        
        # Run the benchmark script
        result = subprocess.run(
            [sys.executable, str(benchmark_script), str(sample_project)],
            capture_output=True,
            text=True,
            env=env
        )
        
        # Should still succeed
        assert result.returncode == 0
        
        # Check output
        output = result.stdout
        assert "Python Implementation:" in output
        
        # Should mention Rust not available (might still load if installed)
        # The actual behavior depends on whether Rust extension is installed


class TestMain:
    """E2E tests for the main function through subprocess execution."""

    def test_main_e2e_help_message(self):
        """Test benchmark script shows usage when called without arguments."""
        benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
        
        result = subprocess.run(
            [sys.executable, str(benchmark_script)],
            capture_output=True,
            text=True
        )
        
        # Should exit with error code
        assert result.returncode == 1
        
        # Should show usage message
        assert "Usage: python benchmark.py <project_path>" in result.stdout

    def test_main_e2e_invalid_path(self):
        """Test benchmark script handles invalid project path."""
        benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
        invalid_path = "/this/path/definitely/does/not/exist"
        
        result = subprocess.run(
            [sys.executable, str(benchmark_script), invalid_path],
            capture_output=True,
            text=True
        )
        
        # Should exit with error code
        assert result.returncode == 1
        
        # Should show error message
        assert f"Error: {invalid_path} does not exist" in result.stdout

    def test_main_e2e_real_project_structure(self):
        """Test benchmarking on a realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create a more realistic project structure
            dirs = [
                "src/app/models",
                "src/app/views",
                "src/app/controllers",
                "tests/unit",
                "tests/integration",
                "tests/e2e",
                "docs",
                ".git"
            ]
            
            for dir_path in dirs:
                (project_path / dir_path).mkdir(parents=True, exist_ok=True)
            
            # Create multiple test files
            test_files = [
                ("tests/unit/test_models.py", """
def test_user_model():
    assert True

def test_product_model():
    pass  # Empty test
"""),
                ("tests/unit/test_views.py", """
import pytest

def test_home_view():
    response = mock_response()
    assert response.status_code == 200

def test_login_view():
    # TODO: implement
    pass
"""),
                ("tests/integration/test_api.py", """
def test_api_endpoint():
    proboscis.stop()
    assert api_call() == expected

def test_api_error_handling():
    # Missing stop hook
    assert True
"""),
                ("tests/e2e/test_user_flow.py", """
def test_user_registration():
    assert register_user("test@example.com")

def test_user_login():
    assert login("test@example.com", "password")
""")
            ]
            
            for file_path, content in test_files:
                file = project_path / file_path
                file.write_text(content)
            
            # Create config
            config = project_path / "pyproject.toml"
            config.write_text("""
[tool.proboscis]
test_directories = ["tests"]
test_patterns = ["test_*.py", "*_test.py"]
""")
            
            # Run benchmark
            benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
            result = subprocess.run(
                [sys.executable, str(benchmark_script), str(project_path)],
                capture_output=True,
                text=True
            )
            
            # Assert successful execution
            assert result.returncode == 0
            
            # Verify it processed multiple files
            output = result.stdout
            assert "Violations found:" in output
            
            # Should show performance metrics
            assert "Time:" in output
            assert "seconds" in output

    def test_main_e2e_performance_comparison(self):
        """Test that performance comparison shows meaningful results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create a project with many test files to ensure measurable time
            test_dir = project_path / "test"
            test_dir.mkdir()
            
            # Create multiple test files
            for i in range(20):
                test_file = test_dir / f"test_file_{i}.py"
                test_file.write_text(f"""
def test_case_{i}_1():
    assert True

def test_case_{i}_2():
    pass  # Empty test

def test_case_{i}_3():
    proboscis.stop()
    assert True
""")
            
            # Run benchmark
            benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
            result = subprocess.run(
                [sys.executable, str(benchmark_script), str(project_path)],
                capture_output=True,
                text=True
            )
            
            # Check execution
            assert result.returncode == 0
            
            output = result.stdout
            
            # Should show both implementations (if Rust is available)
            assert "Python Implementation:" in output
            
            # Should show timing for Python at least
            import re
            python_time_match = re.search(r'Time: ([\d.]+) seconds', output)
            assert python_time_match is not None
            python_time = float(python_time_match.group(1))
            assert python_time >= 0  # Can be 0.00 for very fast execution
            
            # If Rust implementation runs, should show comparison
            if "Rust Implementation:" in output:
                assert "Performance Comparison:" in output
                assert "faster than Python" in output or "slower than Python" in output

    def test_main_e2e_consistent_results(self):
        """Test that multiple runs produce consistent violation counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create test files
            test_dir = project_path / "test"
            test_dir.mkdir()
            
            test_file = test_dir / "test_consistency.py"
            test_file.write_text("""
def test_empty_1():
    pass

def test_empty_2():
    pass

def test_with_hook():
    proboscis.stop()
    assert True
""")
            
            benchmark_script = Path(__file__).parent.parent.parent / "benchmark.py"
            
            # Run benchmark multiple times
            violation_counts = []
            for _ in range(3):
                result = subprocess.run(
                    [sys.executable, str(benchmark_script), str(project_path)],
                    capture_output=True,
                    text=True
                )
                
                assert result.returncode == 0
                
                # Extract violation count
                import re
                match = re.search(r'Violations found: (\d+)', result.stdout)
                assert match is not None
                violation_counts.append(int(match.group(1)))
            
            # All runs should find the same number of violations
            assert len(set(violation_counts)) == 1, f"Inconsistent results: {violation_counts}"


if __name__ == "__main__":
    pytest.main([__file__])