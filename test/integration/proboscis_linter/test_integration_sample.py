"""Integration tests for sample module."""
import pytest
from proboscis_linter.sample import add, subtract, multiply, divide, complex_function


# Direct test function expected by the linter
def test_complex_function():
    """Test complex_function in integration context."""
    # Test with calculated inputs
    x = add(2, 3)  # 5
    y = subtract(10, 7)  # 3
    z = multiply(2, 4)  # 8
    result = complex_function(x, y, z)
    assert result == 16  # 5 + 3 + 8


class TestSampleIntegration:
    """Integration tests for sample module functions working together."""
    
    def test_arithmetic_operations_chain(self):
        """Test chaining multiple arithmetic operations."""
        # (5 + 3) * 2 - 4 = 12
        result1 = add(5, 3)
        result2 = multiply(result1, 2)
        result3 = subtract(result2, 4)
        assert result3 == 12
        
        # (10 - 5) * 4 + 2 = 22
        result1 = subtract(10, 5)
        result2 = multiply(result1, 4)
        result3 = add(result2, 2)
        assert result3 == 22
    
    def test_division_with_other_operations(self):
        """Test division combined with other operations."""
        # (20 / 4) + 5 = 10
        result1 = divide(20, 4)
        result2 = add(result1, 5)
        assert result2 == 10.0
        
        # 100 / (10 - 5) = 20
        denominator = subtract(10, 5)
        result = divide(100, denominator)
        assert result == 20.0
        
        # (15 + 5) / (8 - 4) = 5
        numerator = add(15, 5)
        denominator = subtract(8, 4)
        result = divide(numerator, denominator)
        assert result == 5.0
    
    def test_complex_function_with_calculated_inputs(self):
        """Test complex_function using results from other functions."""
        # Use arithmetic results as inputs to complex_function
        x = add(2, 3)  # 5
        y = subtract(10, 7)  # 3
        z = multiply(2, 4)  # 8
        
        result = complex_function(x, y, z)
        assert result == 16  # 5 + 3 + 8 (x > 0, y > 0)
        
        # Negative inputs
        x = subtract(5, 10)  # -5
        y = subtract(3, 8)  # -5
        z = add(10, 5)  # 15
        
        result = complex_function(x, y, z)
        assert result == 25  # -(-5) - (-5) + 15 (x < 0, y < 0)
    
    def test_error_propagation(self):
        """Test error handling across function combinations."""
        # Division by zero in a chain
        zero_result = subtract(5, 5)  # 0
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, zero_result)
        
        # Complex calculation that would result in division by zero
        a = add(3, 2)  # 5
        b = multiply(1, 5)  # 5
        c = subtract(a, b)  # 0
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(100, c)
    
    def test_mathematical_properties(self):
        """Test mathematical properties using the functions."""
        # Commutative property of addition
        assert add(5, 3) == add(3, 5)
        
        # Commutative property of multiplication
        assert multiply(4, 7) == multiply(7, 4)
        
        # Distributive property: a * (b + c) = (a * b) + (a * c)
        a, b, c = 3, 4, 5
        left_side = multiply(a, add(b, c))
        right_side = add(multiply(a, b), multiply(a, c))
        assert left_side == right_side
        
        # Identity properties
        assert add(5, 0) == 5
        assert multiply(5, 1) == 5
        assert divide(5, 1) == 5.0
    
    def test_complex_calculations(self):
        """Test more complex mathematical calculations."""
        # Calculate average: (a + b + c) / 3
        a, b, c = 10, 20, 30
        sum_abc = add(add(a, b), c)
        average = divide(sum_abc, 3)
        assert average == 20.0
        
        # Calculate percentage: (part / whole) * 100
        part = 25
        whole = 100
        ratio = divide(part, whole)
        percentage = multiply(ratio, 100)
        assert percentage == 25.0
        
        # Quadratic-like calculation: ax² + bx + c
        # Let's calculate 2x² + 3x + 1 where x = 4
        x = 4
        a, b, c = 2, 3, 1
        
        x_squared = multiply(x, x)  # 16
        ax_squared = multiply(a, x_squared)  # 32
        bx = multiply(b, x)  # 12
        result = add(add(ax_squared, bx), c)  # 32 + 12 + 1 = 45
        assert result == 45
    
    def test_complex_function_combinations(self):
        """Test complex_function with various calculated inputs."""
        # Test all branches with calculated values
        test_cases = [
            # (x_calc, y_calc, z_calc, expected_branch)
            (add(1, 2), add(2, 3), multiply(2, 3), "x>0,y>0"),  # 3, 5, 6
            (add(2, 3), subtract(1, 5), add(1, 1), "x>0,y<0"),  # 5, -4, 2
            (subtract(2, 5), add(3, 4), multiply(3, 3), "x<0,y>0"),  # -3, 7, 9
            (subtract(1, 3), subtract(2, 4), add(5, 5), "x<0,y<0"),  # -2, -2, 10
        ]
        
        expected_results = [
            14,  # 3 + 5 + 6
            11,  # 5 - (-4) + 2
            19,  # -(-3) + 7 + 9
            14,  # -(-2) - (-2) + 10
        ]
        
        for (x, y, z, branch), expected in zip(test_cases, expected_results):
            result = complex_function(x, y, z)
            assert result == expected, f"Failed for branch {branch}"
    
    def test_precision_and_rounding(self):
        """Test precision in calculations involving division."""
        # Test that division maintains float precision
        result = divide(10, 3)
        # Use this result in further calculations
        multiplied = multiply(result, 3)
        # Should be close to 10 (accounting for float precision)
        assert abs(multiplied - 10) < 0.0001
        
        # Complex calculation with multiple divisions
        a = divide(100, 7)  # ~14.2857
        b = divide(50, 3)   # ~16.6667
        c = add(a, b)       # ~30.9524
        d = multiply(c, 2)  # ~61.9048
        e = divide(d, 4)    # ~15.4762
        
        # Verify the result is within expected range
        assert 15.4 < e < 15.5
    
    def test_stress_calculations(self):
        """Test functions with many operations."""
        # Factorial-like calculation using repeated multiplication
        result = 1
        for i in range(1, 6):  # 5!
            result = multiply(result, i)
        assert result == 120
        
        # Sum of arithmetic sequence using repeated addition
        sum_result = 0
        for i in range(1, 11):  # Sum of 1 to 10
            sum_result = add(sum_result, i)
        assert sum_result == 55
        
        # Complex nested calculations
        result = complex_function(
            add(multiply(2, 3), subtract(10, 5)),  # 6 + 5 = 11
            subtract(divide(20, 4), multiply(1, 2)),  # 5 - 2 = 3
            add(add(1, 2), add(3, 4))  # 3 + 7 = 10
        )
        assert result == 24  # 11 + 3 + 10 (x > 0, y > 0)