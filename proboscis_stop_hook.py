#!/usr/bin/env python3
"""Stop hook to ensure pytest with testmon passes and coverage is above 90%."""
import json
import sys
import subprocess
import re
from pathlib import Path


def main():
    # Read hook input
    try:
        data = json.load(sys.stdin)
    except:
        data = {}
    
    # Don't create infinite loops
    if data.get("stop_hook_active"):
        sys.exit(0)
    
    # Run pytest with coverage (no testmon for accurate coverage)
    result = subprocess.run(
        ["uv", "run", "pytest", "--no-testmon", "--cov", "--cov-report=term", "--cov-fail-under=90"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    # Extract coverage percentage from output
    coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
    coverage_percent = int(coverage_match.group(1)) if coverage_match else 0
    
    # Check for failures
    has_test_failures = result.returncode != 0
    coverage_below_90 = coverage_percent < 90
    
    if has_test_failures or coverage_below_90:
        # Build reason message
        reasons = []
        if has_test_failures:
            # Extract failure summary
            failure_lines = []
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if "FAILED" in line or "ERROR" in line:
                    failure_lines.append(line.strip())
            reasons.append(f"Tests failed:\n" + '\n'.join(failure_lines[:5]))
        
        if coverage_below_90:
            reasons.append(f"Coverage is {coverage_percent}% (minimum required: 90%)")
        
        # Return block decision with continue
        output = {
            "decision": "block",
            "reason": "\n\n".join(reasons),
            "continue": True,
            "suppressOutput": False
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)
    
    # All good - allow stop
    print(json.dumps({
        "decision": "approve",
        "reason": f"✅ All tests passing with {coverage_percent}% coverage"
    }))


if __name__ == "__main__":
    main()