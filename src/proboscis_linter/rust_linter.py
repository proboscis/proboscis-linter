"""Python wrapper for Rust linter implementation."""
from pathlib import Path
from typing import List, Optional
from loguru import logger

from .models import LintViolation
from .config import ProboscisConfig

try:
    from . import proboscis_linter_rust
    RUST_AVAILABLE = True
except ImportError:
    logger.warning("Rust extension not available, falling back to Python implementation")
    RUST_AVAILABLE = False


class RustLinterWrapper:
    """Wrapper for the Rust linter implementation."""
    
    def __init__(self, config: ProboscisConfig):
        if not RUST_AVAILABLE:
            raise ImportError("Rust extension not built. Run 'maturin develop' to build it.")
        
        self._rust_linter = proboscis_linter_rust.RustLinter(
            test_directories=config.test_directories,
            test_patterns=config.test_patterns,
            exclude_patterns=config.exclude_patterns
        )
        self._config = config
    
    def lint_project(self, project_root: Path) -> List[LintViolation]:
        """Lint a project using the Rust implementation."""
        with logger.contextualize(project_root=str(project_root)):
            logger.info(f"Linting project with Rust implementation: {project_root}")
            
            # Call Rust implementation
            rust_violations = self._rust_linter.lint_project(str(project_root))
            
            # Convert Rust violations to Python models
            violations = []
            for rv in rust_violations:
                # Filter by enabled rules
                rule_id = rv.rule_name.split(':')[0]
                if not self._config.is_rule_enabled(rule_id):
                    continue
                
                violation = LintViolation(
                    rule_name=rv.rule_name,
                    file_path=Path(rv.file_path),
                    line_number=rv.line_number,
                    function_name=rv.function_name,
                    message=rv.message,
                    severity=rv.severity
                )
                violations.append(violation)
            
            logger.info(f"Found {len(violations)} violations")
            return violations
    
    def lint_file(self, file_path: Path, test_directories: List[Path]) -> List[LintViolation]:
        """Lint a single file using the Rust implementation."""
        rust_violations = self._rust_linter.lint_file(str(file_path))
        
        violations = []
        for rv in rust_violations:
            rule_id = rv.rule_name.split(':')[0]
            if not self._config.is_rule_enabled(rule_id):
                continue
            
            violation = LintViolation(
                rule_name=rv.rule_name,
                file_path=Path(rv.file_path),
                line_number=rv.line_number,
                function_name=rv.function_name,
                message=rv.message,
                severity=rv.severity
            )
            violations.append(violation)
        
        return violations
    
    def lint_changed_files(self, project_root: Path) -> List[LintViolation]:
        """Lint only files with git changes using the Rust implementation."""
        with logger.contextualize(project_root=str(project_root)):
            logger.info(f"Linting changed files with Rust implementation: {project_root}")
            
            # Call Rust implementation
            rust_violations = self._rust_linter.lint_changed_files(str(project_root))
            
            # Convert Rust violations to Python models
            violations = []
            for rv in rust_violations:
                # Filter by enabled rules
                rule_id = rv.rule_name.split(':')[0]
                if not self._config.is_rule_enabled(rule_id):
                    continue
                
                violation = LintViolation(
                    rule_name=rv.rule_name,
                    file_path=Path(rv.file_path),
                    line_number=rv.line_number,
                    function_name=rv.function_name,
                    message=rv.message,
                    severity=rv.severity
                )
                violations.append(violation)
            
            logger.info(f"Found {len(violations)} violations in changed files")
            return violations