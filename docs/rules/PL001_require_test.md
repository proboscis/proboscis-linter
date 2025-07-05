# PL001: Require Test

## Summary

Every public function must have a corresponding test.

## Rule Details

This rule ensures that all public functions in your codebase have at least one test function that validates their behavior. This helps maintain code quality and prevents regressions.

### What triggers this rule

A violation is triggered when:
- A public function (not starting with `_`) is found
- No corresponding test function is found in the test directories
- The function is not exempt (see exemptions below)

### What does NOT trigger this rule

The following functions are automatically exempt:
- Private functions (names starting with `_`)
- Constructor methods (`__init__`)
- Protocol methods (methods in classes inheriting from `Protocol`)
- Functions with a `# noqa: PL001` comment

## Examples

### Incorrect

```python
# src/calculator.py
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# No test file exists for this function
```

### Correct

```python
# src/calculator.py
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# tests/test_calculator.py
def test_add():
    from src.calculator import add
    assert add(2, 3) == 5
```

### Using exemptions

```python
# src/utils.py
def temporary_hack():  # noqa: PL001
    """This function is temporary and doesn't need tests."""
    pass
```

## Test Discovery

The rule looks for tests using the following patterns:
- Test files: `test_<module>.py` or `<module>_test.py`
- Test functions: `test_<function_name>` or variations like `test_<function>_<scenario>`
- Test directories: `tests/`, `test/`, or any directory specified in configuration

### Special cases

1. **Class methods**: For a method like `MyClass.my_method`, the rule looks for:
   - `test_my_method`
   - `test_MyClass_my_method`
   - `test_my_class_my_method`

2. **E2E tests**: Functions can also be tested in `e2e/` directories with patterns like:
   - `test_e2e_<function_name>`
   - `e2e_test_<function_name>`

## Configuration

Currently, this rule has no configuration options. It is always enabled when running proboscis-linter.

## When to suppress

You should only suppress this rule in exceptional cases:
- Temporary code that will be removed soon
- Generated code that is tested elsewhere
- Simple data classes or configuration objects

Always include a comment explaining why the test is not needed when using `# noqa: PL001`.