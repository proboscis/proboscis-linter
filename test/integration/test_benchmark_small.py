"""Integration tests for benchmark_small module."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
sys.path.insert(0, '.')
from benchmark_small import main


def test_main():
    """Test the main function integration with real file system."""
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create some test files
        (test_path / "test1.py").write_text("print('test')")
        (test_path / "test2.py").write_text("def foo(): pass")
        
        # Test successful execution with real path
        with patch('sys.argv', ['benchmark_small.py', str(test_path)]):
            # Mock only the Rust components since they require compilation
            with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                with patch('builtins.print') as mock_print:
                    # Setup mock
                    mock_instance = Mock()
                    mock_instance.lint_project.return_value = [
                        {'file': 'test1.py', 'line': 1, 'message': 'violation1'},
                        {'file': 'test2.py', 'line': 1, 'message': 'violation2'}
                    ]
                    mock_rust_linter.return_value = mock_instance
                    
                    main()
                    
                    # Verify the linter was called with the actual path
                    mock_instance.lint_project.assert_called_once()
                    call_args = mock_instance.lint_project.call_args[0][0]
                    assert str(call_args) == str(test_path)
                    
                    # Verify output structure
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any(f"Benchmarking Rust linter on: {test_path}" in call for call in print_calls)
                    assert any("Rust Implementation:" in call for call in print_calls)
                    assert any("Time:" in call for call in print_calls)
                    assert any("Violations found: 2" in call for call in print_calls)
    
    # Test with missing argument (integration with sys.argv)
    original_argv = sys.argv.copy()
    try:
        sys.argv = ['benchmark_small.py']
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit):
                    main()
                mock_exit.assert_called_with(1)
                assert any("Usage:" in str(call) for call in mock_print.call_args_list)
    finally:
        sys.argv = original_argv


def test_main_with_complex_project_structure():
    """Test with a more complex project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create nested directory structure
        (test_path / "src").mkdir()
        (test_path / "src" / "module1.py").write_text("class MyClass: pass")
        (test_path / "src" / "module2.py").write_text("def function(): return 42")
        
        (test_path / "tests").mkdir()
        (test_path / "tests" / "test_module1.py").write_text("import pytest")
        
        (test_path / "__init__.py").write_text("")
        
        with patch('sys.argv', ['benchmark_small.py', str(test_path)]):
            with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                with patch('builtins.print') as mock_print:
                    mock_instance = Mock()
                    # Simulate finding violations in nested files
                    mock_instance.lint_project.return_value = [
                        {'file': 'src/module1.py', 'line': 1, 'violation': 'missing docstring'},
                        {'file': 'src/module2.py', 'line': 1, 'violation': 'missing docstring'},
                        {'file': 'tests/test_module1.py', 'line': 1, 'violation': 'unused import'}
                    ]
                    mock_rust_linter.return_value = mock_instance
                    
                    main()
                    
                    # Verify it processed the complex structure
                    mock_instance.lint_project.assert_called_once()
                    assert any("Violations found: 3" in str(call) for call in mock_print.call_args_list)


def test_main_config_loading():
    """Test configuration loading in integration context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create a config file in the project
        config_content = """
[tool.proboscis]
exclude = ["tests/*", "*.pyc"]
max_line_length = 120
"""
        (test_path / "pyproject.toml").write_text(config_content)
        (test_path / "main.py").write_text("print('hello')")
        
        with patch('sys.argv', ['benchmark_small.py', str(test_path)]):
            # Patch RustLinterWrapper but let ProboscisConfig load naturally
            with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                mock_instance = Mock()
                mock_instance.lint_project.return_value = []
                mock_rust_linter.return_value = mock_instance
                
                main()
                
                # Verify config was passed to RustLinterWrapper
                mock_rust_linter.assert_called_once()
                config_arg = mock_rust_linter.call_args[0][0]
                # Should be an instance of ProboscisConfig
                assert hasattr(config_arg, '__class__')
                assert config_arg.__class__.__name__ == 'ProboscisConfig'


def test_main_import_error_handling():
    """Test ImportError handling in integration context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        with patch('sys.argv', ['benchmark_small.py', str(test_path)]):
            # Simulate Rust extension not being available
            with patch('benchmark_small.RustLinterWrapper', side_effect=ImportError("No module named 'proboscis_linter_rust'")):
                with patch('builtins.print') as mock_print:
                    # Should not raise, but print error message
                    main()
                    
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Rust implementation not available:" in call for call in print_calls)
                    assert any("Run 'maturin develop'" in call for call in print_calls)


def test_main_performance_measurement():
    """Test that performance measurement works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create files to lint
        for i in range(10):
            (test_path / f"file{i}.py").write_text(f"# File {i}\nprint({i})")
        
        with patch('sys.argv', ['benchmark_small.py', str(test_path)]):
            with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                # Use actual time but mock the linter
                mock_instance = Mock()
                
                # Simulate some processing time by adding a small delay
                def mock_lint_project(path):
                    import time
                    time.sleep(0.01)  # 10ms delay
                    return [f"violation_{i}" for i in range(5)]
                
                mock_instance.lint_project = mock_lint_project
                mock_rust_linter.return_value = mock_instance
                
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Check that timing was measured
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    
                    # Should have printed time and processing speed
                    time_prints = [call for call in print_calls if "Time:" in call]
                    speed_prints = [call for call in print_calls if "Processing speed:" in call]
                    
                    assert len(time_prints) > 0
                    assert len(speed_prints) > 0
                    
                    # Time should be at least 0.01 seconds
                    for time_print in time_prints:
                        if "Time: " in time_print:
                            # Extract the time value
                            import re
                            match = re.search(r'Time: ([\d.]+) seconds', time_print)
                            if match:
                                time_value = float(match.group(1))
                                assert time_value >= 0.01