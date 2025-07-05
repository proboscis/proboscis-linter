"""End-to-end tests for calculator module."""

def test_e2e_calculate_total():
    """Test calculate_total method end-to-end."""
    from src.calculator import Calculator
    
    calc = Calculator()
    items = [
        {'name': 'apple', 'price': 1.50},
        {'name': 'banana', 'price': 0.75},
        {'name': 'orange', 'price': 2.00}
    ]
    
    total = calc.calculate_total(items)
    assert total == 4.25