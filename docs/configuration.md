# Configuration Guide

Proboscis-linter can be configured through your project's `pyproject.toml` file under the `[tool.proboscis]` section.

## Configuration File Location

The linter searches for `pyproject.toml` by traversing up the directory tree from the target path. It will use the first file found that contains a `[tool.proboscis]` section.

## Configuration Options

### Basic Example

```toml
[tool.proboscis]
test_directories = ["test", "tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = ["**/migrations/**", "**/__pycache__/**"]
output_format = "text"
fail_on_error = false

[tool.proboscis.rules]
PL001 = true  # Enable the require-test rule
```

### Full Configuration Reference

#### Test Discovery

- **`test_directories`** (list of strings): Directories to search for test files
  - Default: `["test", "tests"]`
  - Example: `["test", "tests", "spec"]`

- **`test_patterns`** (list of strings): File patterns for test discovery
  - Default: `["test_*.py", "*_test.py"]`
  - Example: `["test_*.py", "*_test.py", "*_spec.py"]`

#### File Filtering

- **`exclude_patterns`** (list of strings): Glob patterns for files/directories to exclude from linting
  - Default: `[]`
  - Example: `["**/migrations/**", "**/__pycache__/**", "**/vendor/**"]`

#### Output Configuration

- **`output_format`** (string): Default output format
  - Options: `"text"` or `"json"`
  - Default: `"text"`

- **`fail_on_error`** (boolean): Exit with non-zero code if violations are found
  - Default: `false`

#### Rule Configuration

Rules can be configured in two ways:

1. **Simple enable/disable**:
   ```toml
   [tool.proboscis.rules]
   PL001 = true   # Enable
   PL002 = false  # Disable
   ```

2. **Detailed configuration** (for future rules with options):
   ```toml
   [tool.proboscis.rules.PL001]
   enabled = true
   options = {
       # Rule-specific options here
   }
   ```

## CLI Options Override

Command-line options take precedence over configuration file settings:

```bash
# Override output format
proboscis-lint --format json

# Override fail-on-error
proboscis-lint --fail-on-error

# Add additional exclude patterns
proboscis-lint --exclude "**/generated/**" --exclude "**/build/**"
```

## Example Configurations

### Minimal Configuration

```toml
[tool.proboscis]
# Use all defaults, just enable the tool
```

### Django Project

```toml
[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = [
    "**/migrations/**",
    "**/management/commands/**",
    "**/static/**",
    "**/templates/**"
]
fail_on_error = true
```

### Monorepo with Multiple Test Directories

```toml
[tool.proboscis]
test_directories = ["tests", "test", "spec", "tests/unit", "tests/integration"]
test_patterns = ["test_*.py", "*_test.py", "*_spec.py"]
exclude_patterns = [
    "**/node_modules/**",
    "**/vendor/**",
    "**/third_party/**"
]
```

### Strict Mode

```toml
[tool.proboscis]
fail_on_error = true
output_format = "json"  # For CI integration

[tool.proboscis.rules]
# Explicitly enable all rules
PL001 = true
```

## Disabling Rules for Specific Functions

Even with rules enabled in configuration, you can disable them for specific functions using comments:

```python
def temporary_function():  # noqa: PL001
    """This function doesn't need tests."""
    pass
```