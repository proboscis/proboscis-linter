"""Integration tests for calculator module."""

@pytest.mark.integration
def test_integration_divide():
    """Test divide function with various inputs."""
    from src.calculator import divide
    assert divide(10, 2) == 5
    assert divide(15, 3) == 5
    
    # Test error case
    try:
        divide(10, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass