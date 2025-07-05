from pathlib import Path
import json
import pytest
from proboscis_linter.models import LintViolation
from proboscis_linter.report_generator import TextReportGenerator, JsonReportGenerator


def test_text_report_generator_empty():
    generator = TextReportGenerator()
    report = generator.generate_report([])
    
    assert "No violations found" in report
    assert "✓" in report


def test_text_report_generator_with_violations():
    violations = [
        LintViolation(
            rule_name="PL001:require-test",
            file_path=Path("src/module1.py"),
            line_number=10,
            function_name="func1",
            message="[PL001] Function 'func1' has no test found",
            severity="error"
        ),
        LintViolation(
            rule_name="PL001:require-test",
            file_path=Path("src/module2.py"),
            line_number=20,
            function_name="func2",
            message="[PL001] Function 'func2' has no test found",
            severity="error"
        )
    ]
    
    generator = TextReportGenerator()
    report = generator.generate_report(violations)
    
    assert "Found 2 violations" in report
    assert "src/module1.py:10" in report
    assert "func1" in report
    assert "src/module2.py:20" in report
    assert "func2" in report
    assert "ERROR" in report


def test_json_report_generator():
    violations = [
        LintViolation(
            rule_name="PL001:require-test",
            file_path=Path("src/module.py"),
            line_number=10,
            function_name="func1",
            message="[PL001] Function 'func1' has no test found",
            severity="error"
        )
    ]
    
    generator = JsonReportGenerator()
    report = generator.generate_report(violations)
    
    data = json.loads(report)
    assert data["total_violations"] == 1
    assert len(data["violations"]) == 1
    assert data["violations"][0]["rule"] == "PL001:require-test"
    assert data["violations"][0]["function"] == "func1"
    assert data["violations"][0]["severity"] == "error"


def test_report_generator_names():
    text_gen = TextReportGenerator()
    json_gen = JsonReportGenerator()
    
    assert text_gen.get_format_name() == "text"
    assert json_gen.get_format_name() == "json"