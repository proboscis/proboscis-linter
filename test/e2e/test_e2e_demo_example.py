"""End-to-end tests for demo_example.py"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo_example import untested_function, exempt_function, MyClass


class TestDemoExampleE2E:
    """End-to-end tests for demo_example module."""
    
    @pytest.mark.e2e
    def test_untested_function(self):
        """E2E test for untested_function."""
        # Act - simulate real usage
        result = untested_function()
        
        # Assert
        assert result == "untested"
        assert isinstance(result, str)
    
    @pytest.mark.e2e
    def test_exempt_function(self):
        """E2E test for exempt_function."""
        # Act - simulate real usage
        result = exempt_function()
        
        # Assert
        assert result == "exempt"
        assert isinstance(result, str)
    
    @pytest.mark.e2e
    def test_MyClass_public_method(self):
        """E2E test for MyClass public_method."""
        # Simulate real-world usage scenario
        my_instance = MyClass()
        
        # Initial state check
        initial_result = my_instance.public_method()
        assert initial_result == 0
        
        # Simulate setting value and using the method
        my_instance.value = 42
        result = my_instance.public_method()
        assert result == 84
    
    @pytest.mark.e2e
    def test_complete_workflow(self):
        """Test a complete workflow using multiple components."""
        # Create instance
        calculator = MyClass()
        
        # Get function results
        untested_result = untested_function()
        exempt_result = exempt_function()
        
        # Use class method with different values
        calculator.value = 10
        calc_result1 = calculator.public_method()
        
        calculator.value = 25
        calc_result2 = calculator.public_method()
        
        # Assert all results
        assert untested_result == "untested"
        assert exempt_result == "exempt"
        assert calc_result1 == 20
        assert calc_result2 == 50
    
    @pytest.mark.e2e
    def test_MyClass_lifecycle(self):
        """Test complete lifecycle of MyClass usage."""
        # Create and use instance
        obj = MyClass()
        assert obj.value == 0
        
        # Perform multiple operations
        operations = [
            (1, 2),
            (5, 10),
            (0, 0),
            (-1, -2),
            (100, 200)
        ]
        
        for input_val, expected_output in operations:
            obj.value = input_val
            assert obj.public_method() == expected_output


if __name__ == "__main__":
    pytest.main([__file__])