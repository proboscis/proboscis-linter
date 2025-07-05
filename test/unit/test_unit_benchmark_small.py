"""Unit tests for benchmark_small module."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
sys.path.insert(0, '.')
from benchmark_small import main


def test_main():
    """Test the main function of benchmark_small."""
    # Test with missing command line argument
    with patch('sys.argv', ['benchmark_small.py']):
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit):
                    main()
                mock_print.assert_called_with("Usage: python benchmark_small.py <project_path>")
                mock_exit.assert_called_with(1)
    
    # Test with non-existent project path
    with patch('sys.argv', ['benchmark_small.py', '/non/existent/path']):
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit):
                    main()
                mock_print.assert_called_with("Error: /non/existent/path does not exist")
                mock_exit.assert_called_with(1)
    
    # Test successful execution with mocked components
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    
    with patch('sys.argv', ['benchmark_small.py', '/test/path']):
        with patch('benchmark_small.Path', return_value=mock_path):
            with patch('benchmark_small.ProboscisConfig') as mock_config:
                with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                    with patch('benchmark_small.time.time', side_effect=[100.0, 102.0]):
                        with patch('builtins.print') as mock_print:
                            # Setup mock
                            mock_instance = Mock()
                            mock_instance.lint_project.return_value = ['violation1', 'violation2']
                            mock_rust_linter.return_value = mock_instance
                            
                            main()
                            
                            # Verify calls
                            mock_config.assert_called_once()
                            mock_rust_linter.assert_called_once_with(mock_config.return_value)
                            mock_instance.lint_project.assert_called_once_with(mock_path)
                            
                            # Verify output
                            print_calls = mock_print.call_args_list
                            assert any("Benchmarking Rust linter on:" in str(call) for call in print_calls)
                            assert any("Rust Implementation:" in str(call) for call in print_calls)
                            assert any("Time: 2.00 seconds" in str(call) for call in print_calls)
                            assert any("Violations found: 2" in str(call) for call in print_calls)
                            assert any("Processing speed: 386 files/second" in str(call) for call in print_calls)
    
    # Test ImportError handling
    with patch('sys.argv', ['benchmark_small.py', '/test/path']):
        with patch('benchmark_small.Path', return_value=mock_path):
            with patch('benchmark_small.ProboscisConfig'):
                with patch('benchmark_small.RustLinterWrapper', side_effect=ImportError("Module not found")):
                    with patch('builtins.print'):
                        main()
                        
                        print_calls = mock_print.call_args_list
                        assert any("Rust implementation not available: Module not found" in str(call) for call in print_calls)
                        assert any("Run 'maturin develop' to build the Rust extension" in str(call) for call in print_calls)


def test_main_edge_cases():
    """Test edge cases for the main function."""
    # Test with empty violations list
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    
    with patch('sys.argv', ['benchmark_small.py', '/test/path']):
        with patch('benchmark_small.Path', return_value=mock_path):
            with patch('benchmark_small.ProboscisConfig'):
                with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                    with patch('benchmark_small.time.time', side_effect=[100.0, 100.1]):
                        with patch('builtins.print') as mock_print:
                            # Setup mock with empty violations
                            mock_instance = Mock()
                            mock_instance.lint_project.return_value = []
                            mock_rust_linter.return_value = mock_instance
                            
                            main()
                            
                            # Verify output for empty violations
                            print_calls = mock_print.call_args_list
                            assert any("Violations found: 0" in str(call) for call in print_calls)
                            assert any("Time: 0.10 seconds" in str(call) for call in print_calls)
                            assert any("Processing speed: 7720 files/second" in str(call) for call in print_calls)


def test_main_performance_edge_case():
    """Test performance calculation edge cases."""
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    
    # Test with very fast execution (near zero time)
    with patch('sys.argv', ['benchmark_small.py', '/test/path']):
        with patch('benchmark_small.Path', return_value=mock_path):
            with patch('benchmark_small.ProboscisConfig'):
                with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                    with patch('benchmark_small.time.time', side_effect=[100.0, 100.001]):
                        with patch('builtins.print') as mock_print:
                            mock_instance = Mock()
                            mock_instance.lint_project.return_value = []
                            mock_rust_linter.return_value = mock_instance
                            
                            main()
                            
                            # Should handle very small durations gracefully
                            print_calls = mock_print.call_args_list
                            assert any("Time: 0.00 seconds" in str(call) for call in print_calls)
                            assert any("Processing speed: 772000 files/second" in str(call) for call in print_calls)


def test_main_rust_linter_exception():
    """Test handling of exceptions from RustLinterWrapper."""
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    
    with patch('sys.argv', ['benchmark_small.py', '/test/path']):
        with patch('benchmark_small.Path', return_value=mock_path):
            with patch('benchmark_small.ProboscisConfig'):
                with patch('benchmark_small.RustLinterWrapper') as mock_rust_linter:
                    with patch('builtins.print'):
                        # Test lint_project throwing exception
                        mock_instance = Mock()
                        mock_instance.lint_project.side_effect = RuntimeError("Linting failed")
                        mock_rust_linter.return_value = mock_instance
                        
                        # Should not catch RuntimeError, only ImportError
                        with pytest.raises(RuntimeError, match="Linting failed"):
                            main()