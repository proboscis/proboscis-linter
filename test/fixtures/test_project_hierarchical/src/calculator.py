"""Test module for verifying proboscis-linter rule splitting."""

def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    def __init__(self):
        self.memory = 0
    
    def calculate_total(self, items):
        """Calculate total price of items."""
        return sum(item['price'] for item in items)