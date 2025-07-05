"""Unit tests for sample module."""
import pytest
from proboscis_linter.sample import add, subtract, multiply, divide, complex_function


# Direct test functions expected by the linter
def test_divide():
    """Test divide function."""
    assert divide(10, 2) == 5.0
    assert divide(20, 4) == 5.0
    with pytest.raises(ValueError):
        divide(10, 0)


def test_complex_function():
    """Test complex_function."""
    assert complex_function(1, 1, 1) == 3
    assert complex_function(5, -3, 2) == 10
    assert complex_function(-5, 3, 2) == 10
    assert complex_function(-5, -3, 2) == 10


class TestAdd:
    """Test the add function."""
    
    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(2, 3) == 5
        assert add(10, 20) == 30
        assert add(1, 1) == 2
    
    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        assert add(-5, -3) == -8
        assert add(-10, -20) == -30
        assert add(-1, -1) == -2
    
    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        assert add(5, -3) == 2
        assert add(-5, 3) == -2
        assert add(10, -10) == 0
    
    def test_add_with_zero(self):
        """Test adding with zero."""
        assert add(0, 0) == 0
        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(-5, 0) == -5
    
    def test_add_large_numbers(self):
        """Test adding large numbers."""
        assert add(1000000, 2000000) == 3000000
        assert add(999999, 1) == 1000000


class TestSubtract:
    """Test the subtract function."""
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        assert subtract(5, 3) == 2
        assert subtract(10, 5) == 5
        assert subtract(100, 50) == 50
    
    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        assert subtract(-5, -3) == -2
        assert subtract(-3, -5) == 2
        assert subtract(-10, -10) == 0
    
    def test_subtract_mixed_numbers(self):
        """Test subtracting mixed sign numbers."""
        assert subtract(5, -3) == 8
        assert subtract(-5, 3) == -8
        assert subtract(0, -5) == 5
    
    def test_subtract_with_zero(self):
        """Test subtracting with zero."""
        assert subtract(0, 0) == 0
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5
    
    def test_subtract_same_numbers(self):
        """Test subtracting same numbers."""
        assert subtract(5, 5) == 0
        assert subtract(-5, -5) == 0
        assert subtract(100, 100) == 0


class TestMultiply:
    """Test the multiply function."""
    
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        assert multiply(2, 3) == 6
        assert multiply(5, 4) == 20
        assert multiply(10, 10) == 100
    
    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        assert multiply(-2, -3) == 6
        assert multiply(-5, -4) == 20
        assert multiply(-10, -10) == 100
    
    def test_multiply_mixed_numbers(self):
        """Test multiplying positive and negative numbers."""
        assert multiply(2, -3) == -6
        assert multiply(-2, 3) == -6
        assert multiply(5, -1) == -5
    
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        assert multiply(0, 0) == 0
        assert multiply(5, 0) == 0
        assert multiply(0, 5) == 0
        assert multiply(-5, 0) == 0
        assert multiply(0, -5) == 0
    
    def test_multiply_by_one(self):
        """Test multiplying by one."""
        assert multiply(5, 1) == 5
        assert multiply(1, 5) == 5
        assert multiply(-5, 1) == -5
        assert multiply(1, -5) == -5


class TestDivide:
    """Test the divide function."""
    
    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        assert divide(10, 2) == 5.0
        assert divide(20, 4) == 5.0
        assert divide(100, 10) == 10.0
    
    def test_divide_negative_numbers(self):
        """Test dividing negative numbers."""
        assert divide(-10, -2) == 5.0
        assert divide(-20, -4) == 5.0
        assert divide(-100, -10) == 10.0
    
    def test_divide_mixed_numbers(self):
        """Test dividing positive and negative numbers."""
        assert divide(10, -2) == -5.0
        assert divide(-10, 2) == -5.0
        assert divide(20, -4) == -5.0
    
    def test_divide_decimal_results(self):
        """Test division resulting in decimals."""
        assert divide(10, 3) == pytest.approx(3.333333, rel=1e-5)
        assert divide(7, 2) == 3.5
        assert divide(1, 3) == pytest.approx(0.333333, rel=1e-5)
    
    def test_divide_by_one(self):
        """Test dividing by one."""
        assert divide(5, 1) == 5.0
        assert divide(-5, 1) == -5.0
        assert divide(0, 1) == 0.0
    
    def test_divide_zero_numerator(self):
        """Test dividing zero by a number."""
        assert divide(0, 5) == 0.0
        assert divide(0, -5) == 0.0
        assert divide(0, 100) == 0.0
    
    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(-10, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(0, 0)


class TestComplexFunction:
    """Test the complex_function with multiple branches."""
    
    def test_complex_function_all_positive(self):
        """Test when x > 0 and y > 0."""
        assert complex_function(1, 1, 1) == 3
        assert complex_function(5, 3, 2) == 10
        assert complex_function(10, 20, 30) == 60
    
    def test_complex_function_positive_x_negative_y(self):
        """Test when x > 0 and y <= 0."""
        assert complex_function(5, -3, 2) == 10  # 5 - (-3) + 2 = 5 + 3 + 2
        assert complex_function(10, -5, 3) == 18  # 10 - (-5) + 3 = 10 + 5 + 3
        assert complex_function(1, 0, 1) == 2  # 1 - 0 + 1
    
    def test_complex_function_negative_x_positive_y(self):
        """Test when x <= 0 and y > 0."""
        assert complex_function(-5, 3, 2) == 10  # -(-5) + 3 + 2 = 5 + 3 + 2
        assert complex_function(0, 5, 3) == 8  # -0 + 5 + 3 = 0 + 5 + 3
        assert complex_function(-10, 20, 5) == 35  # -(-10) + 20 + 5 = 10 + 20 + 5
    
    def test_complex_function_all_negative(self):
        """Test when x <= 0 and y <= 0."""
        assert complex_function(-5, -3, 2) == 10  # -(-5) - (-3) + 2 = 5 + 3 + 2
        assert complex_function(0, 0, 5) == 5  # -0 - 0 + 5 = 0 + 0 + 5
        assert complex_function(-10, -20, 30) == 60  # -(-10) - (-20) + 30 = 10 + 20 + 30
    
    def test_complex_function_edge_cases(self):
        """Test edge cases with zeros."""
        assert complex_function(0, 0, 0) == 0
        assert complex_function(1, 0, 0) == 1  # x > 0, y = 0
        assert complex_function(0, 1, 0) == 1  # x = 0, y > 0
        assert complex_function(-1, 0, 0) == 1  # x < 0, y = 0
        assert complex_function(0, -1, 0) == 1  # x = 0, y < 0
    
    def test_complex_function_with_large_values(self):
        """Test with large values."""
        assert complex_function(1000, 2000, 3000) == 6000
        assert complex_function(-1000, -2000, 3000) == 6000
        assert complex_function(1000, -2000, 3000) == 6000
        assert complex_function(-1000, 2000, 3000) == 6000