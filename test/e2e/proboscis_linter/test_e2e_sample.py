"""End-to-end tests for sample module."""
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest
from proboscis_linter.sample import add, subtract, multiply, divide, complex_function


# Direct test function expected by the linter
def test_complex_function():
    """Test complex_function in e2e context."""
    # Test in a real-world scenario
    result = complex_function(10, 5, 2)
    assert result == 17  # 10 + 5 + 2
    
    # Test error case
    result = complex_function(-10, -5, 100)
    assert result == 115  # -(-10) - (-5) + 100 = 10 + 5 + 100


class TestSampleE2E:
    """End-to-end tests for sample module in realistic scenarios."""
    
    def test_calculator_simulation(self):
        """Simulate a calculator application using the sample functions."""
        # Simulate a series of calculator operations
        calculator_memory = 0
        
        # User enters: 10
        calculator_memory = 10
        
        # User presses: + 5
        calculator_memory = add(calculator_memory, 5)
        assert calculator_memory == 15
        
        # User presses: * 2
        calculator_memory = multiply(calculator_memory, 2)
        assert calculator_memory == 30
        
        # User presses: - 10
        calculator_memory = subtract(calculator_memory, 10)
        assert calculator_memory == 20
        
        # User presses: / 4
        calculator_memory = divide(calculator_memory, 4)
        assert calculator_memory == 5.0
        
        # Clear and start new calculation
        calculator_memory = 0
        
        # Complex calculation: (25 + 15) * 3 - 20 / 4
        temp1 = add(25, 15)  # 40
        temp2 = multiply(temp1, 3)  # 120
        temp3 = divide(20, 4)  # 5
        result = subtract(temp2, temp3)  # 115
        assert result == 115.0
    
    def test_financial_calculations(self):
        """Test sample functions in financial calculation scenarios."""
        # Calculate simple interest: Principal * Rate * Time / 100
        principal = 1000
        rate = 5
        time = 2
        
        interest_numerator = multiply(multiply(principal, rate), time)
        interest = divide(interest_numerator, 100)
        assert interest == 100.0
        
        # Calculate total amount
        total = add(principal, interest)
        assert total == 1100.0
        
        # Calculate profit margin: ((Revenue - Cost) / Revenue) * 100
        revenue = 5000
        cost = 3500
        
        profit = subtract(revenue, cost)  # 1500
        margin_ratio = divide(profit, revenue)  # 0.3
        margin_percentage = multiply(margin_ratio, 100)  # 30
        assert margin_percentage == 30.0
        
        # Calculate compound calculations
        initial_investment = 1000
        yearly_return = 10  # 10%
        years = 3
        
        # Year 1
        year1_return = divide(multiply(initial_investment, yearly_return), 100)
        year1_total = add(initial_investment, year1_return)  # 1100
        
        # Year 2
        year2_return = divide(multiply(year1_total, yearly_return), 100)
        year2_total = add(year1_total, year2_return)  # 1210
        
        # Year 3
        year3_return = divide(multiply(year2_total, yearly_return), 100)
        year3_total = add(year2_total, year3_return)  # 1331
        
        assert year3_total == 1331.0
    
    def test_scientific_calculations(self):
        """Test sample functions in scientific calculation scenarios."""
        # Calculate velocity: distance / time
        distance = 100  # meters
        time = 20  # seconds
        velocity = divide(distance, time)
        assert velocity == 5.0  # m/s
        
        # Calculate force: mass * acceleration
        mass = 10  # kg
        acceleration = 2  # m/s²
        force = multiply(mass, acceleration)
        assert force == 20  # Newtons
        
        # Calculate kinetic energy: 0.5 * mass * velocity²
        velocity_squared = multiply(velocity, velocity)
        kinetic_energy = multiply(0.5, multiply(mass, velocity_squared))
        assert kinetic_energy == 125.0  # Joules
        
        # Temperature conversion using complex_function
        # Simulate different conversion scenarios
        celsius = 25
        
        # Celsius to Fahrenheit: (C * 9/5) + 32
        temp1 = multiply(celsius, 9)
        temp2 = divide(temp1, 5)
        fahrenheit = add(temp2, 32)
        assert fahrenheit == 77.0
    
    def test_game_score_calculations(self):
        """Test sample functions in a game scoring system."""
        # Basic scoring system
        base_score = 100
        multiplier = 3
        bonus = 50
        penalty = 20
        
        # Calculate score with multiplier
        multiplied_score = multiply(base_score, multiplier)
        
        # Add bonus
        score_with_bonus = add(multiplied_score, bonus)
        
        # Apply penalty
        final_score = subtract(score_with_bonus, penalty)
        assert final_score == 330
        
        # Complex scoring with complex_function
        # Different scoring rules based on performance
        performance = 8  # Good performance
        difficulty = 5  # Medium difficulty
        time_bonus = 15
        
        # Use complex_function for dynamic scoring
        dynamic_score = complex_function(performance, difficulty, time_bonus)
        assert dynamic_score == 28  # 8 + 5 + 15 (performance > 0, difficulty > 0)
        
        # Poor performance scenario
        performance = -2  # Negative performance
        difficulty = -1  # Easy mode (negative difficulty)
        time_bonus = 10
        
        dynamic_score = complex_function(performance, difficulty, time_bonus)
        assert dynamic_score == 13  # -(-2) - (-1) + 10
    
    def test_data_analysis_calculations(self):
        """Test sample functions in data analysis scenarios."""
        # Calculate mean of a dataset
        data = [10, 20, 30, 40, 50]
        
        # Sum all values
        total = 0
        for value in data:
            total = add(total, value)
        assert total == 150
        
        # Calculate mean
        mean = divide(total, len(data))
        assert mean == 30.0
        
        # Calculate variance steps
        squared_differences = []
        for value in data:
            diff = subtract(value, mean)
            squared_diff = multiply(diff, diff)
            squared_differences.append(squared_diff)
        
        # Sum squared differences
        sum_squared_diff = 0
        for sq_diff in squared_differences:
            sum_squared_diff = add(sum_squared_diff, sq_diff)
        
        # Variance
        variance = divide(sum_squared_diff, len(data))
        assert variance == 200.0
        
        # Calculate range
        min_value = min(data)
        max_value = max(data)
        data_range = subtract(max_value, min_value)
        assert data_range == 40
    
    def test_error_handling_in_applications(self):
        """Test error handling in realistic application scenarios."""
        # Scenario 1: User input validation for division
        user_inputs = [
            (10, 2),  # Valid
            (20, 0),  # Division by zero
            (15, 3),  # Valid
        ]
        
        results = []
        errors = []
        
        for numerator, denominator in user_inputs:
            try:
                result = divide(numerator, denominator)
                results.append(result)
            except ValueError as e:
                errors.append(str(e))
        
        assert len(results) == 2
        assert len(errors) == 1
        assert results == [5.0, 5.0]
        assert "Cannot divide by zero" in errors[0]
        
        # Scenario 2: Safe calculation chain
        def safe_calculate(a, b, c):
            """Safely calculate (a + b) / c with error handling."""
            try:
                sum_ab = add(a, b)
                result = divide(sum_ab, c)
                return result, None
            except ValueError as e:
                return None, str(e)
        
        # Test various inputs
        test_cases = [
            (10, 20, 5),  # Valid: 30/5 = 6
            (5, 5, 0),    # Error: 10/0
            (0, 0, 1),    # Valid: 0/1 = 0
        ]
        
        for a, b, c in test_cases:
            result, error = safe_calculate(a, b, c)
            if c == 0:
                assert result is None
                assert error == "Cannot divide by zero"
            else:
                assert error is None
                assert result == divide(add(a, b), c)
    
    def test_performance_with_many_operations(self):
        """Test performance with many operations."""
        import time
        
        # Measure time for many operations
        start_time = time.time()
        
        # Perform 10000 mixed operations
        result = 0
        for i in range(1000):
            result = add(result, i)
            result = multiply(result, 1.001)
            result = subtract(result, 0.5)
            if i % 10 == 0 and i > 0:
                result = divide(result, 2)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (under 1 second)
        assert execution_time < 1.0
        
        # Verify result is reasonable
        assert result > 0
    
    def test_module_as_library(self):
        """Test using the sample module as a library in scripts."""
        # Create a temporary Python script that uses the sample module
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "use_sample.py"
            script_path.write_text("""
import sys
sys.path.insert(0, '.')
from proboscis_linter.sample import add, multiply, divide

# Simple calculation script
a = 10
b = 20
c = 5

result1 = add(a, b)
result2 = multiply(result1, c)
result3 = divide(result2, 10)

print(f"Result: {result3}")
print(f"Success: {result3 == 15.0}")
""")
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            # Check script executed successfully
            assert result.returncode == 0
            assert "Result: 15.0" in result.stdout
            assert "Success: True" in result.stdout