import sys
from pathlib import Path
import click
from loguru import logger

from .linter import ProboscisLinter
from .report_generator import TextReportGenerator, JsonReportGenerator
from .config import ProboscisConfig, ConfigLoader

# Version info
__version__ = "0.1.0"


# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> <level>{level: <8}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@click.command(
    name="proboscis-lint",
    context_settings=dict(help_option_names=["-h", "--help"]),
    epilog="""
\b
EXAMPLES:
  # Lint current directory
  proboscis-linter .
  
  # Lint specific directory with JSON output
  proboscis-linter src/ --format json
  
  # Lint only changed files in git
  proboscis-linter . --changed-only
  
  # Exclude test files and fail on violations
  proboscis-linter . --exclude "tests/**" --fail-on-error
  
  # Verbose output for debugging
  proboscis-linter . -v

\b
RULES:
  PL001: require-unit-test
    Ensures each function has a corresponding unit test in test/unit/
    
  PL002: require-integration-test  
    Ensures each function has a corresponding integration test in test/integration/
    
  PL003: require-e2e-test
    Ensures each function has a corresponding end-to-end test in test/e2e/

\b
TEST NAMING CONVENTIONS:
  The linter expects test functions to follow these naming patterns:
  
  For a function: def process_data(x, y):
  Expected tests: test_process_data, test_process_data_*
  
  For a method: class DataProcessor: def process(self):
  Expected tests: test_process, test_DataProcessor_process, test_process_*
  
  Test files should mirror the source structure:
  src/module.py → test/unit/test_module.py
  src/utils/helper.py → test/unit/test_helper.py

\b
SUPPRESSING VIOLATIONS:
  Use #noqa comments to suppress specific rules on individual functions:
  
  def my_function():  #noqa PL001
      # This function won't trigger PL001 violations
      pass
  
  def another_function():  #noqa: PL001, PL002
      # Suppresses both PL001 and PL002
      pass

\b
CONFIGURATION:
  Create a pyproject.toml file with [tool.proboscis] section:
  
  [tool.proboscis]
  test_directories = ["test", "tests"]
  exclude_patterns = ["**/migrations/**", "**/__pycache__/**"]
  
  [tool.proboscis.rules]
  PL001 = true
  PL002 = false  # Disable integration test requirement
  PL003 = true

\b
For more information, visit: https://github.com/proboscis/proboscis-linter
"""
)
@click.argument(
    "path", 
    type=click.Path(exists=True, path_type=Path), 
    default=".",
    metavar="[PATH]"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format for violations report. 'text' for human-readable output, 'json' for machine-parseable output.",
    show_default=True
)
@click.option(
    "--fail-on-error",
    is_flag=True,
    help="Exit with non-zero status code (1) if any violations are found. Useful for CI/CD pipelines."
)
@click.option(
    "--exclude", "-e",
    multiple=True,
    help="Glob pattern for files to exclude from linting. Can be specified multiple times. Example: --exclude '**/migrations/**' --exclude '**/test_*.py'",
    metavar="PATTERN"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging output. Shows detailed information about which files are being checked and why violations occur."
)
@click.option(
    "--changed-only", "-c",
    is_flag=True,
    help="Only check files that have been modified in git (includes staged, unstaged, and untracked Python files). Requires the project to be in a git repository."
)
@click.version_option(
    __version__,
    "--version", "-V",
    message="%(prog)s version %(version)s",
    help="Show the version and exit."
)
def cli(path: Path, format: str, fail_on_error: bool, exclude: tuple, verbose: bool, changed_only: bool):
    """
    Proboscis Linter - A fast, Rust-powered linter that ensures all Python functions have corresponding tests.
    
    \b
    This linter helps maintain high test coverage by enforcing that every function 
    and method in your Python codebase has associated unit, integration, and/or 
    end-to-end tests. It's designed to be fast, accurate, and easy to integrate
    into your development workflow.
    
    PATH: Directory or file to lint (defaults to current directory)
    """
    
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Load configuration
    config_file = ConfigLoader.find_config_file(path)
    if config_file:
        config = ConfigLoader.load_from_file(config_file)
    else:
        config = ProboscisConfig()
    
    # Merge CLI options
    config = ConfigLoader.merge_cli_options(
        config,
        format=format,
        fail_on_error=fail_on_error,
        exclude=list(exclude) if exclude else None
    )
    
    # Create linter with configuration (uses Rust implementation by default)
    linter = ProboscisLinter(config)
    
    # Lint the project
    if changed_only:
        logger.info(f"Linting changed files in {path}...")
        violations = linter.lint_changed_files(path)
    else:
        logger.info(f"Linting {path}...")
        violations = linter.lint_project(path)
    
    # Generate report
    if config.output_format == "json":
        generator = JsonReportGenerator()
    else:
        generator = TextReportGenerator()
    
    report = generator.generate_report(violations)
    click.echo(report)
    
    # Exit with appropriate code
    if config.fail_on_error and violations:
        sys.exit(1)


if __name__ == "__main__":
    cli()