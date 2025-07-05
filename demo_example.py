"""Demo file to show linter functionality"""
from typing import Protocol


def function_with_test():
    """This function has a test - no violation"""
    return 42


def untested_function():
    """This function has no test - will show violation"""
    return "untested"


def exempt_function():  # noqa: PL001
    """This function is exempt from testing requirement"""
    return "exempt"


class MyClass:
    def __init__(self):
        """Constructor - automatically skipped"""
        self.value = 0
    
    def _private_method(self):
        """Private method - automatically skipped"""
        return self.value
    
    def public_method(self):
        """Public method needs a test"""
        return self.value * 2


class IMyProtocol(Protocol):
    def protocol_method(self) -> str:
        """Protocol methods are automatically skipped"""
        ...