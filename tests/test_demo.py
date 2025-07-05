"""Tests for demo_example.py"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from demo_example import function_with_test


def test_function_with_test():
    """Test for function_with_test"""
    assert function_with_test() == 42