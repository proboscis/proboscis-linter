"""Module demonstrating structured test requirements."""

def standalone_function():
    """A standalone function that needs tests."""
    return 42


class Calculator:
    """A class with methods that need tests."""
    
    def __init__(self):
        self.memory = 0
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
    
    def update(self, value):
        """Update memory with a new value."""
        self.memory = value
        return self.memory


class DataProcessor:
    """Another class to demonstrate naming."""
    
    def process(self, data):
        """Process some data."""
        return data.upper() if isinstance(data, str) else data
    
    def update(self, config):
        """Update configuration - same method name as Calculator.update."""
        self.config = config