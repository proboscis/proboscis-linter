"""Integration tests for demo_example.py"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo_example import untested_function, exempt_function, MyClass


class TestUntestedFunctionIntegration:
    """Integration tests for untested_function."""
    
    @pytest.mark.integration
    def test_untested_function(self):
        """Test untested_function in integration context."""
        # Act
        result = untested_function()
        
        # Assert
        assert result == "untested"
        assert isinstance(result, str)
        assert len(result) > 0


class TestExemptFunctionIntegration:
    """Integration tests for exempt_function."""
    
    @pytest.mark.integration
    def test_exempt_function(self):
        """Test exempt_function returns expected value."""
        # Act
        result = exempt_function()
        
        # Assert
        assert result == "exempt"
        assert isinstance(result, str)
        assert len(result) > 0


class TestMyClassIntegration:
    """Integration tests for MyClass."""
    
    @pytest.mark.integration
    def test_MyClass_public_method(self):
        """Test MyClass public_method in integration context."""
        # Arrange
        instance = MyClass()
        
        # Test initial state
        assert instance.value == 0
        assert instance.public_method() == 0
        
        # Test after value change
        instance.value = 10
        result = instance.public_method()
        
        # Assert
        assert result == 20
    
    @pytest.mark.integration
    def test_MyClass_multiple_instances(self):
        """Test multiple MyClass instances work independently."""
        # Arrange
        instance1 = MyClass()
        instance2 = MyClass()
        
        # Modify one instance
        instance1.value = 5
        instance2.value = 3
        
        # Act
        result1 = instance1.public_method()
        result2 = instance2.public_method()
        
        # Assert
        assert result1 == 10
        assert result2 == 6
        assert instance1.value != instance2.value
    
    @pytest.mark.integration
    def test_MyClass_state_persistence(self):
        """Test that MyClass maintains state correctly."""
        # Arrange
        instance = MyClass()
        
        # Act & Assert - multiple operations
        instance.value = 1
        assert instance.public_method() == 2
        
        instance.value = 5
        assert instance.public_method() == 10
        
        instance.value = -2
        assert instance.public_method() == -4


if __name__ == "__main__":
    pytest.main([__file__])