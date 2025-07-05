"""Unit tests for calculator module."""

@pytest.mark.unit
def test_add():
    """Test add function."""
    from src.calculator import add
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

@pytest.mark.unit
def test_unit_multiply():
    """Test multiply function."""
    from src.calculator import multiply
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0