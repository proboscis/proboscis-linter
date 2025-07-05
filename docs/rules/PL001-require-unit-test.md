# PL001: require-unit-test

## Summary

Every function should have a corresponding unit test to ensure code correctness at the function level.

## Description

This rule enforces that every non-private function has at least one corresponding unit test. Unit tests focus on testing individual functions in isolation, ensuring each piece of functionality works correctly on its own.

## Why This Matters

- **Function-Level Correctness**: Ensures individual functions work as expected
- **Fast Feedback**: Unit tests run quickly, providing immediate feedback
- **Easier Debugging**: When a unit test fails, the problem is localized
- **Refactoring Safety**: Catch regressions at the smallest level

## Examples

### Bad Example

```python
# src/calculator.py
def add(a, b):
    return a + b  # PL001: Function 'add' has no unit test found

def multiply(a, b):
    return a * b  # PL001: Function 'multiply' has no unit test found
```

### Good Example

```python
# src/calculator.py
def add(a, b):
    return a + b  # OK - has test_add in test/unit/test_calculator.py

def multiply(a, b):
    return a * b  # OK - has test_multiply in test/unit/test_calculator.py

# test/unit/test_calculator.py
def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(2, 3) == 6
```

## Test Discovery

The linter looks for unit tests using the following patterns:
- `test_{function_name}`
- `test_unit_{function_name}`
- `test_{class_name}_{function_name}` (for methods)

Unit tests should be placed in the `test/unit/` directory.

## Exceptions

The following functions are automatically excluded:
- Private functions (starting with `_`)
- `__init__` methods
- Protocol methods (methods in Protocol classes)

## Disabling the Rule

You can disable this rule for specific functions using:

```python
def external_api_function():  # noqa: PL001
    pass  # This might be tested by integration tests instead
```

Or disable it globally in `pyproject.toml`:

```toml
[tool.proboscis.rules]
PL001 = false
```