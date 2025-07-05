"""Unit tests for __main__ module."""
import pytest
from unittest.mock import patch, Mock
from proboscis_linter.__main__ import main


class TestMain:
    """Test the main function."""
    
    @pytest.mark.unit
    def test_main_calls_cli(self):
        """Test that main() calls the cli function."""
        with patch('proboscis_linter.__main__.cli') as mock_cli:
            main()
            mock_cli.assert_called_once()
    
    @pytest.mark.unit
    def test_main_with_arguments(self):
        """Test main() passes through command line arguments."""
        test_args = ['proboscis-linter', 'src/', '--format', 'json']
        
        with patch('sys.argv', test_args):
            with patch('proboscis_linter.__main__.cli') as mock_cli:
                main()
                mock_cli.assert_called_once()
    
    @pytest.mark.unit
    def test_main_handles_cli_exception(self):
        """Test main() handles exceptions from cli."""
        with patch('proboscis_linter.__main__.cli') as mock_cli:
            mock_cli.side_effect = Exception("Test error")
            
            # main() should not crash, but let the exception propagate
            with pytest.raises(Exception, match="Test error"):
                main()
    
    @pytest.mark.unit
    def test_main_keyboard_interrupt(self):
        """Test main() handles KeyboardInterrupt gracefully."""
        with patch('proboscis_linter.__main__.cli') as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()
            
            # Should propagate the KeyboardInterrupt
            with pytest.raises(KeyboardInterrupt):
                main()
    
    @pytest.mark.unit
    def test_main_system_exit(self):
        """Test main() handles SystemExit."""
        with patch('proboscis_linter.__main__.cli') as mock_cli:
            mock_cli.side_effect = SystemExit(1)
            
            # Should propagate SystemExit
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @pytest.mark.unit
    def test_main_no_arguments(self):
        """Test main() with no command line arguments."""
        with patch('sys.argv', ['proboscis-linter']):
            with patch('proboscis_linter.__main__.cli') as mock_cli:
                main()
                mock_cli.assert_called_once()
    
    @pytest.mark.unit
    def test_main_help_argument(self):
        """Test main() with help argument."""
        with patch('sys.argv', ['proboscis-linter', '--help']):
            with patch('proboscis_linter.__main__.cli') as mock_cli:
                # Mock cli to simulate help display
                mock_cli.side_effect = SystemExit(0)
                
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_cli.assert_called_once()


class TestMainModule:
    """Test the __main__ module execution."""
    
    @pytest.mark.unit
    def test_module_imports(self):
        """Test that required imports are available."""
        from proboscis_linter.__main__ import cli, main
        assert callable(cli)
        assert callable(main)
    
    @pytest.mark.unit
    def test_main_module_execution(self):
        """Test execution when module is run directly."""
        with patch('proboscis_linter.__main__.main') as mock_main:
            # Simulate running the module
            with patch('proboscis_linter.__main__.__name__', '__main__'):
                # Need to re-execute the module code
                import importlib
                import proboscis_linter.__main__
                importlib.reload(proboscis_linter.__main__)
                
                # main() should have been called
                mock_main.assert_called()