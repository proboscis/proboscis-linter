# PL004: require-test-markers

## Overview

The `PL004` rule ensures that all test functions have the appropriate pytest marker based on their location in the test hierarchy. This helps maintain consistency and enables better test organization and filtering.

## Requirements

Test functions must have the following pytest markers based on their directory:

- Tests in `test/unit/` → `@pytest.mark.unit`
- Tests in `test/integration/` → `@pytest.mark.integration`
- Tests in `test/e2e/` → `@pytest.mark.e2e`

## Examples

### ❌ Incorrect

```python
# File: test/unit/test_calculator.py

def test_add():  # Missing @pytest.mark.unit
    assert add(1, 2) == 3

@pytest.mark.integration  # Wrong marker for unit test
def test_multiply():
    assert multiply(2, 3) == 6
```

### ✅ Correct

```python
# File: test/unit/test_calculator.py
import pytest

@pytest.mark.unit
def test_add():
    assert add(1, 2) == 3

@pytest.mark.unit
def test_multiply():
    assert multiply(2, 3) == 6
```

## Marker Formats

The rule recognizes various marker formats:

```python
import pytest
from pytest import mark

# Full form (recommended)
@pytest.mark.unit
def test_full_form():
    pass

# Short form
@mark.unit
def test_short_form():
    pass

# Multiple markers
@pytest.mark.unit
@pytest.mark.slow
def test_multiple_markers():
    pass
```

## Configuration

You can disable this rule in your `pyproject.toml`:

```toml
[tool.proboscis.rules]
PL004 = false
```

## Suppressing Violations

### File-level suppression

```python
# noqa: PL004

def test_special_case():
    # All tests in this file will skip PL004 checks
    pass
```

### Line-level suppression

```python
def test_special_case():  # noqa: PL004
    # Only this test will skip PL004 check
    pass
```

## Benefits

1. **Test Organization**: Clear separation between test types
2. **Test Filtering**: Easy to run specific test types with pytest markers
3. **CI/CD Integration**: Can run different test suites in different stages
4. **Consistency**: Enforces team conventions for test categorization

## Running Specific Test Types

With proper markers, you can easily filter tests:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Run all except e2e tests
pytest -m "not e2e"
```

## pytest Configuration

To make the markers official in your project, add them to `pytest.ini`:

```ini
[pytest]
markers =
    unit: Unit tests that test individual functions/methods
    integration: Integration tests that test component interactions
    e2e: End-to-end tests that test full workflows
```