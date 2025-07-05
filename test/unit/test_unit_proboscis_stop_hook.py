"""Unit tests for proboscis_stop_hook.py."""
import json
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the parent directory to the path to import proboscis_stop_hook
sys.path.insert(0, '/Users/s22625/repos/proboscis-linter')


@pytest.mark.unit
def test_main_successful_run():
    """Test successful test run with coverage above 90%."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """
---------- coverage: platform darwin, python 3.12.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               50      2    95%
---------------------------------------------
TOTAL                        50      2    95%
"""
    
    # Import and patch the module's subprocess reference
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'approve'
    assert '95%' in output['reason']


@pytest.mark.unit
def test_main_test_failures():
    """Test failures with coverage still high."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = """
FAILED tests/test_example.py::test_two - AssertionError

---------- coverage: platform darwin, python 3.12.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               50      2    95%
---------------------------------------------
TOTAL                        50      2    95%
"""
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'block'
    assert 'Tests failed' in output['reason']
    assert output['continue'] is True


@pytest.mark.unit
def test_main_low_coverage():
    """Test coverage below 90%."""
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = """
---------- coverage: platform darwin, python 3.12.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               50     10    80%
---------------------------------------------
TOTAL                        50     10    80%
"""
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'block'
    assert 'Coverage is 80%' in output['reason']


@pytest.mark.unit
def test_main_both_failures_and_low_coverage():
    """Test both failures and low coverage."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = """
FAILED tests/test_example.py::test_two - AssertionError
ERROR tests/test_example.py::test_three - RuntimeError

---------- coverage: platform darwin, python 3.12.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               50     20    60%
---------------------------------------------
TOTAL                        50     20    60%
"""
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'block'
    assert 'Tests failed' in output['reason']
    assert 'Coverage is 60%' in output['reason']
    # Check that it found both FAILED and ERROR lines
    assert 'FAILED tests/test_example.py::test_two' in output['reason']
    assert 'ERROR tests/test_example.py::test_three' in output['reason']


@pytest.mark.unit
def test_main_no_coverage_match():
    """Test no coverage match (default to 0%)."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "No coverage data found"
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'block'
    assert 'Coverage is 0%' in output['reason']


@pytest.mark.unit
def test_main_stop_hook_active():
    """Test that stop_hook_active prevents execution."""
    import proboscis_stop_hook
    with patch('sys.stdin', StringIO('{"stop_hook_active": true}')):
        with patch('sys.exit') as mock_exit:
            proboscis_stop_hook.main()
            mock_exit.assert_called_once_with(0)


@pytest.mark.unit
def test_main_invalid_json():
    """Test handling of invalid JSON input."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """
---------- coverage: platform darwin, python 3.12.0 ----------
TOTAL                        50      2    95%
"""
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('invalid json')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    # Should still work with empty data dict
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'approve'


@pytest.mark.unit
def test_main_no_failures_in_stdout():
    """Test when returncode indicates failure but no FAILED lines in output."""
    mock_result = MagicMock()
    mock_result.returncode = 1  # Non-zero indicates failure
    mock_result.stdout = """
---------- coverage: platform darwin, python 3.12.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               50      2    95%
---------------------------------------------
TOTAL                        50      2    95%
"""
    
    import proboscis_stop_hook
    with patch.object(proboscis_stop_hook.subprocess, 'run', return_value=mock_result):
        with patch('sys.stdin', StringIO('{}')):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit'):
                    proboscis_stop_hook.main()
    
    output = json.loads(mock_print.call_args[0][0])
    assert output['decision'] == 'block'
    assert 'Tests failed' in output['reason']
    # When no FAILED lines found, reason should have empty list of failures
    assert output['reason'] == 'Tests failed:\n'


@pytest.mark.unit
def test_main():
    """Run all test cases for backward compatibility."""
    test_main_successful_run()
    test_main_test_failures()
    test_main_low_coverage()
    test_main_both_failures_and_low_coverage()
    test_main_no_coverage_match()
    test_main_stop_hook_active()
    test_main_invalid_json()
    test_main_no_failures_in_stdout()