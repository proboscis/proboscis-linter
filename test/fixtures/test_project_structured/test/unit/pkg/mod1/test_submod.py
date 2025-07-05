"""Unit tests for pkg.mod1.submod module."""

def test_standalone_function():
    """Test the standalone function."""
    from src.pkg.mod1.submod import standalone_function
    assert standalone_function() == 42


def test_Calculator_add():
    """Test Calculator.add method using proper naming convention."""
    from src.pkg.mod1.submod import Calculator
    calc = Calculator()
    assert calc.add(2, 3) == 5


def test_Calculator_multiply():
    """Test Calculator.multiply method."""
    from src.pkg.mod1.submod import Calculator
    calc = Calculator()
    assert calc.multiply(3, 4) == 12


# Note: Calculator.update has no test - should trigger PL001


def test_DataProcessor_process():
    """Test DataProcessor.process method."""
    from src.pkg.mod1.submod import DataProcessor
    proc = DataProcessor()
    assert proc.process("hello") == "HELLO"


# Note: DataProcessor.update has no test - should trigger PL001