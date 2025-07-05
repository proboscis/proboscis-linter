"""Unit tests for calculator module."""

def test_add():
    """Test add function."""
    from src.calculator import add
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_unit_multiply():
    """Test multiply function."""
    from src.calculator import multiply
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0