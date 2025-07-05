# Proboscis Linter

A high-performance Python linter that enforces test coverage for functions and class methods. Built with Rust for speed and Python for ease of use. Supports hierarchical test organization and enforces test structure that mirrors your source code organization.

## Features

- **Fast**: Rust-based implementation processes files in parallel
- **Configurable**: Control rules via `pyproject.toml`
- **Extensible**: Easy to add new rules with the PL### naming convention
- **Smart**: Respects `#noqa` comments (with flexible syntax) and understands test patterns
- **Class-Aware**: Distinguishes between class methods and standalone functions
- **Hierarchical Tests**: Supports unit, integration, and e2e test organization
- **Structure Enforcement**: Tests must mirror source code package structure
- **Git Integration**: Use `--changed-only` to lint only modified files
- **Flexible Suppression**: Support for `#noqa PL001`, `#noqa: PL001`, and `#noqa PL001, PL002`

## Installation

```bash
pip install proboscis-linter
```

For development:
```bash
git clone https://github.com/proboscis/proboscis-linter
cd proboscis-linter
uv pip install -e .
uv run maturin develop  # Build Rust extension
```

## Usage

### Command Line

```bash
# Lint current directory
proboscis-linter .

# Lint specific path
proboscis-linter src/

# JSON output
proboscis-linter --format json

# Fail on violations
proboscis-linter --fail-on-error

# Lint only changed files in git
proboscis-linter . --changed-only

# Show comprehensive help
proboscis-linter --help

# Automatically fix violations (currently supports PL004)
proboscis-linter . --fix
```

### Auto-fix Support

The linter can automatically fix certain violations with the `--fix` flag:

#### Currently Supported Auto-fixes

- **PL004**: Automatically adds missing pytest markers (@pytest.mark.unit/integration/e2e) to test functions

```bash
# Example: Auto-fix missing pytest markers
proboscis-linter test/ --fix

# Before fix:
def test_my_function():
    assert True

# After fix:
@pytest.mark.unit
def test_my_function():
    assert True
```

The auto-fix feature:
- Preserves existing decorators and indentation
- Adds markers above any existing decorators
- Handles class methods with proper indentation
- Re-runs the linter after applying fixes to ensure violations are resolved

### Configuration

Configure via `pyproject.toml`:

```toml
[tool.proboscis]
test_directories = ["test", "tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = ["**/__pycache__/**", "**/migrations/**"]
output_format = "text"
fail_on_error = false
strict_mode = false  # When true, checks private functions too

[tool.proboscis.rules]
PL001 = true  # require-unit-test
PL002 = true  # require-integration-test
PL003 = true  # require-e2e-test
PL004 = true  # require-test-markers
```

## Rules

### PL001: require-unit-test

Ensures all public functions and methods have corresponding unit tests.

**Skip with**: `#noqa PL001` or `#noqa: PL001`

**Test Location**: Tests must be in `test/unit/` directory with matching structure

**Test Naming**:
- Functions: `test_function_name` or `test_unit_function_name`
- Class methods: `test_ClassName_method_name` or `test_classname_method_name`

### PL002: require-integration-test

Ensures functions have integration tests when enabled.

**Skip with**: `#noqa PL002` or `#noqa: PL002`

**Test Location**: Tests must be in `test/integration/` directory

### PL003: require-e2e-test

Ensures functions have end-to-end tests when enabled.

**Skip with**: `#noqa PL003` or `#noqa: PL003`

**Test Location**: Tests must be in `test/e2e/` directory

### PL004: require-test-markers

Ensures test functions have appropriate pytest markers based on their location.

**Skip with**: `#noqa PL004` or `#noqa: PL004`

**Required Markers**:
- Tests in `test/unit/` must have `@pytest.mark.unit`
- Tests in `test/integration/` must have `@pytest.mark.integration`
- Tests in `test/e2e/` must have `@pytest.mark.e2e`

**Auto-fix**: This rule supports automatic fixing with the `--fix` flag

**Skipped by default for all rules**:
- Private functions (starting with `_`) - unless `strict_mode = true`
- Functions not in `__all__` when `__all__` is defined
- `__init__` methods
- Protocol methods
- Functions in test files

## Public API Detection

By default, proboscis-linter only checks public functions and methods:

### Module-level visibility
- If a module defines `__all__`, only functions listed in `__all__` are checked
- If no `__all__` is defined, functions starting with `_` are considered private
- Use `strict_mode = true` to check all functions including private ones

### Class method visibility
- Methods starting with `_` are always considered private (except in strict mode)
- Special methods like `__init__`, `__str__`, etc. are always excluded
- If a class is private (not in `__all__` or starts with `_`), its methods are not checked

### Example

```python
# module.py
__all__ = ['public_func', 'PublicClass']

def public_func():  # Checked - in __all__
    pass

def _private_func():  # Not checked - starts with _
    pass

def internal_func():  # Not checked - not in __all__
    pass

class PublicClass:  # Checked - in __all__
    def method(self):  # Checked
        pass
    
    def _private_method(self):  # Not checked - starts with _
        pass

class _PrivateClass:  # Not checked - starts with _
    def method(self):  # Not checked - class is private
        pass
```

## Test Organization

### Package Structure Mirroring

Tests must be organized to mirror your source code structure. All tests for a module should be in a single test file:

```
# Source file:
src/pkg/mod1/submod.py

# Expected test files:
test/unit/pkg/mod1/test_submod.py       # All unit tests for submod.py
test/integration/pkg/mod1/test_submod.py # All integration tests for submod.py  
test/e2e/pkg/mod1/test_submod.py        # All e2e tests for submod.py
```

### Test Naming Convention

All functions and methods from a source module should have their tests in the corresponding test file:

```python
# Source code in src/pkg/mod1/submod.py
def standalone_function():
    return 42

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

# Test code in test/unit/pkg/mod1/test_submod.py
def test_standalone_function():
    assert standalone_function() == 42

def test_Calculator_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_Calculator_multiply():
    calc = Calculator()
    assert calc.multiply(3, 4) == 12
```

For class methods, the test function name includes the class name: `test_ClassName_method`

## Performance

The Rust implementation provides significant performance improvements:
- **7-8x faster** than pure Python implementations
- Processes 50+ files per second
- Parallel file processing with rayon

## Adding New Rules

See [docs/adding_rules.md](docs/adding_rules.md) for detailed instructions on adding new linting rules.

## Development

### Requirements

- Python 3.8+
- Rust 1.70+
- maturin

### Running Tests

```bash
uv run pytest
```

### Building

```bash
uv run maturin build --release
```

## License

MIT License - see LICENSE file for details.