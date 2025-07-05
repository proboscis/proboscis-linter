"""Tests for sample module."""
import pytest
from proboscis_linter.sample import add, subtract, multiply, divide, complex_function


def test_add():
    """Test add function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtract function."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(-1, -1) == 0


# Intentionally not testing multiply and divide to have low coverage
# def test_multiply():
#     """Test multiply function."""
#     assert multiply(2, 3) == 6
#     assert multiply(-2, 3) == -6
#     assert multiply(0, 5) == 0


# def test_divide():
#     """Test divide function."""
#     assert divide(10, 2) == 5.0
#     assert divide(-10, 2) == -5.0
#     with pytest.raises(ValueError, match="Cannot divide by zero"):
#         divide(10, 0)


# Only testing one branch of complex_function
def test_complex_function_partial():
    """Test only one branch of complex function."""
    assert complex_function(1, 1, 1) == 3  # x > 0, y > 0