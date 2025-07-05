import json
from typing import List, Protocol

from .models import LintViolation


class IReportGenerator(Protocol):
    def generate_report(self, violations: List[LintViolation]) -> str:
        ...
    
    def get_format_name(self) -> str:
        ...


class TextReportGenerator:
    def generate_report(self, violations: List[LintViolation]) -> str:
        if not violations:
            return "✓ No violations found. All functions have tests!"
        
        lines = [f"\nFound {len(violations)} violations:\n"]
        
        for violation in violations:
            lines.append(
                f"  {violation.severity.upper()}: {violation.file_path}:{violation.line_number} "
                f"- {violation.message}"
            )
        
        lines.append(f"\nTotal violations: {len(violations)}")
        return "\n".join(lines)
    
    def get_format_name(self) -> str:
        return "text"


class JsonReportGenerator:
    def generate_report(self, violations: List[LintViolation]) -> str:
        report_data = {
            "total_violations": len(violations),
            "violations": [
                {
                    "rule": violation.rule_name,
                    "function": violation.function_name,
                    "file": str(violation.file_path),
                    "line": violation.line_number,
                    "message": violation.message,
                    "severity": violation.severity
                }
                for violation in violations
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
    def get_format_name(self) -> str:
        return "json"