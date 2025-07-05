from pathlib import Path
from typing import List, Optional
from loguru import logger

from .models import LintViolation
from .config import ProboscisConfig
from .rust_linter import RustLinterWrapper


class ProboscisLinter:
    """Main linter class that uses the Rust implementation for performance."""
    
    def __init__(self, config: Optional[ProboscisConfig] = None):
        self._config = config or ProboscisConfig()
        self._rust_linter = RustLinterWrapper(self._config)
    
    def lint_project(self, project_root: Path) -> List[LintViolation]:
        """Lint an entire project directory."""
        return self._rust_linter.lint_project(project_root)
    
    def lint_file(self, file_path: Path, test_directories: List[Path]) -> List[LintViolation]:
        """Lint a single file."""
        return self._rust_linter.lint_file(file_path, test_directories)