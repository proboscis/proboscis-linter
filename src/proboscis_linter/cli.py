import sys
from pathlib import Path
import click
from loguru import logger

from .linter import ProboscisLinter
from .report_generator import TextReportGenerator, JsonReportGenerator
from .config import ProboscisConfig, ConfigLoader


# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> <level>{level: <8}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@click.command(name="proboscis-lint")
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format for the report"
)
@click.option(
    "--fail-on-error",
    is_flag=True,
    help="Exit with non-zero code if violations are found"
)
@click.option(
    "--exclude",
    multiple=True,
    help="Glob patterns for files to exclude"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--changed-only",
    is_flag=True,
    help="Only check files with git changes (staged, unstaged, or untracked)"
)
def cli(path: Path, format: str, fail_on_error: bool, exclude: tuple, verbose: bool, changed_only: bool):
    """Proboscis Linter - Enforce that all Python functions have tests."""
    
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