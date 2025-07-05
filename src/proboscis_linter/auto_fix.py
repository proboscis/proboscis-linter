"""Auto-fix functionality for proboscis-linter violations."""
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from loguru import logger

from .models import LintViolation


class AutoFixer:
    """Applies automatic fixes for lint violations."""
    
    def __init__(self):
        self.applied_fixes = defaultdict(int)
    
    def apply_fixes(self, violations: List[LintViolation]) -> Dict[str, int]:
        """Apply fixes for violations that have fix information.
        
        Returns:
            Dict mapping file paths to number of fixes applied
        """
        # Group violations by file
        violations_by_file = defaultdict(list)
        for violation in violations:
            if violation.fix_type and violation.fix_content and violation.fix_line:
                violations_by_file[str(violation.file_path)].append(violation)
        
        # Apply fixes to each file
        for file_path, file_violations in violations_by_file.items():
            try:
                self._apply_fixes_to_file(Path(file_path), file_violations)
            except Exception as e:
                logger.error(f"Failed to apply fixes to {file_path}: {e}")
        
        return dict(self.applied_fixes)
    
    def _apply_fixes_to_file(self, file_path: Path, violations: List[LintViolation]):
        """Apply fixes to a single file."""
        # Read the file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Sort violations by line number in reverse order
        # This ensures we don't mess up line numbers when inserting
        sorted_violations = sorted(violations, key=lambda v: v.fix_line, reverse=True)
        
        # Apply each fix
        for violation in sorted_violations:
            if violation.fix_type == "add_decorator":
                self._apply_add_decorator(lines, violation)
                self.applied_fixes[str(file_path)] += 1
        
        # Write the file back
        with open(file_path, 'w') as f:
            f.writelines(lines)
            
        logger.info(f"Applied {self.applied_fixes[str(file_path)]} fixes to {file_path}")
    
    def _apply_add_decorator(self, lines: List[str], violation: LintViolation):
        """Add a decorator above a function."""
        # Find the indentation of the function
        func_line_idx = violation.line_number - 1  # Convert to 0-based
        if func_line_idx < len(lines):
            func_line = lines[func_line_idx]
            indent = self._get_indentation(func_line)
            
            # Check if there are existing decorators
            insert_idx = func_line_idx
            while insert_idx > 0 and lines[insert_idx - 1].strip().startswith('@'):
                insert_idx -= 1
            
            # Insert the decorator with the same indentation
            decorator_line = f"{indent}{violation.fix_content}\n"
            lines.insert(insert_idx, decorator_line)
    
    def _get_indentation(self, line: str) -> str:
        """Extract the indentation from a line."""
        stripped = line.lstrip()
        if stripped:
            return line[:len(line) - len(stripped)]
        return ""