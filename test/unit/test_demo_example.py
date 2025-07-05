"""Unit tests for demo_example.py"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo_example import untested_function, MyClass


class TestUntestedFunction:
    """Unit tests for untested_function."""
    
    def test_untested_function(self):
        """Test that untested_function returns expected value."""
        # Act
        result = untested_function()
        
        # Assert
        assert result == "untested"
        assert isinstance(result, str)


class TestMyClass:
    """Unit tests for MyClass."""
    
    def test_MyClass_public_method(self):
        """Test that public_method returns double the value."""
        # Arrange
        instance = MyClass()
        instance.value = 5
        
        # Act
        result = instance.public_method()
        
        # Assert
        assert result == 10
    
    def test_MyClass_public_method_with_zero(self):
        """Test public_method with zero value."""
        # Arrange
        instance = MyClass()
        instance.value = 0
        
        # Act
        result = instance.public_method()
        
        # Assert
        assert result == 0
    
    def test_MyClass_public_method_with_negative(self):
        """Test public_method with negative value."""
        # Arrange
        instance = MyClass()
        instance.value = -3
        
        # Act
        result = instance.public_method()
        
        # Assert
        assert result == -6
    
    def test_MyClass_initialization(self):
        """Test that MyClass initializes with value 0."""
        # Act
        instance = MyClass()
        
        # Assert
        assert instance.value == 0


if __name__ == "__main__":
    pytest.main([__file__])