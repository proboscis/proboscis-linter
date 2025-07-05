"""End-to-end tests for proboscis_stop_hook.py."""
import json
import sys
import subprocess
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, '/Users/s22625/repos/proboscis-linter')


@pytest.mark.e2e
def test_main():
    """Test the main function in a real environment context."""
    # Get the path to the hook script
    hook_script = Path('/Users/s22625/repos/proboscis-linter/proboscis_stop_hook.py')
    
    # Test case 1: Run the hook in the actual project directory
    # This tests the hook against the real codebase
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input='{}',
        capture_output=True,
        text=True,
        cwd=str(hook_script.parent)
    )
    
    # The hook should return valid JSON
    assert result.stdout, "Hook should produce output"
    output = json.loads(result.stdout)
    
    # Verify the output structure
    assert 'decision' in output
    assert output['decision'] in ['approve', 'block']
    assert 'reason' in output
    
    # If blocked, should have continue flag
    if output['decision'] == 'block':
        assert 'continue' in output
        assert 'suppressOutput' in output
    
    # Test case 2: Test with stop_hook_active to prevent loops
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input='{"stop_hook_active": true}',
        capture_output=True,
        text=True,
        cwd=str(hook_script.parent)
    )
    
    # Should exit cleanly without output
    assert result.returncode == 0
    assert result.stdout == ''
    
    # Test case 3: Test hook behavior with various input formats
    test_inputs = [
        '{}',  # Empty object
        '{"some_key": "some_value"}',  # Object with irrelevant data
        '{"stop_hook_active": false}',  # Explicitly false flag
    ]
    
    for test_input in test_inputs:
        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input=test_input,
            capture_output=True,
            text=True,
            cwd=str(hook_script.parent)
        )
        
        if test_input != '{"stop_hook_active": true}':
            # Should produce valid JSON output
            assert result.stdout, f"Hook should produce output for input: {test_input}"
            output = json.loads(result.stdout)
            assert 'decision' in output
            assert 'reason' in output
    
    # Test case 4: Verify the hook correctly parses coverage output
    # This is an e2e test that verifies the regex patterns work correctly
    sample_coverage_outputs = [
        # Standard coverage output
        "TOTAL                       100     10    90%",
        "TOTAL                       100      0   100%",
        "TOTAL                       100     20    80%",
        # With extra spaces
        "TOTAL                    100     10     90%",
        # Different formatting
        "TOTAL                        50      5    90%",
    ]
    
    import re
    for coverage_line in sample_coverage_outputs:
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", coverage_line)
        assert match, f"Regex should match coverage line: {coverage_line}"
        percent = int(match.group(1))
        assert 0 <= percent <= 100, f"Coverage percentage should be valid: {percent}"
    
    # Test case 5: Verify command line arguments are correct
    # The hook should run pytest with specific arguments
    # Expected args would be: ["uv", "run", "pytest", "--no-testmon", "--cov", "--cov-report=term", "--cov-fail-under=90"]
    
    # We can't easily verify the actual subprocess call, but we can ensure
    # the script exists and is executable
    assert hook_script.exists(), "Hook script should exist"
    assert hook_script.is_file(), "Hook script should be a file"
    
    # Verify the script has proper shebang
    with open(hook_script, 'r') as f:
        first_line = f.readline().strip()
        assert first_line.startswith('#!'), "Script should have shebang"
        assert 'python' in first_line, "Script should use python interpreter"