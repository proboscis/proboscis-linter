"""Sample module for testing coverage."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def complex_function(x: int, y: int, z: int) -> int:
    """A complex function with multiple branches."""
    if x > 0:
        if y > 0:
            return x + y + z
        else:
            return x - y + z
    else:
        if y > 0:
            return -x + y + z
        else:
            return -x - y + z