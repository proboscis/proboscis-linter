# Proboscis Linter

A high-performance Python linter that enforces test coverage for functions. Built with Rust for speed and Python for ease of use.

## Features

- **Fast**: Rust-based implementation processes files in parallel
- **Configurable**: Control rules via `pyproject.toml`
- **Extensible**: Easy to add new rules with the PL### naming convention
- **Smart**: Respects `# noqa` comments and understands test patterns

## Installation

```bash
pip install proboscis-linter
```

For development:
```bash
git clone https://github.com/yourusername/proboscis-linter
cd proboscis-linter
uv pip install -e .
uv run maturin develop  # Build Rust extension
```

## Usage

### Command Line

```bash
# Lint current directory
proboscis-lint

# Lint specific path
proboscis-lint src/

# JSON output
proboscis-lint --format json

# Fail on violations
proboscis-lint --fail-on-error
```

### Configuration

Configure via `pyproject.toml`:

```toml
[tool.proboscis]
test_directories = ["test", "tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = ["**/__pycache__/**", "**/migrations/**"]
output_format = "text"
fail_on_error = false

[tool.proboscis.rules]
PL001 = true  # require-test rule
```

## Rules

### PL001: require-test

Ensures all public functions have corresponding tests.

**Skip with**: `# noqa: PL001`

**Skipped by default**:
- Private functions (starting with `_`)
- `__init__` methods
- Protocol methods
- Functions in test files

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