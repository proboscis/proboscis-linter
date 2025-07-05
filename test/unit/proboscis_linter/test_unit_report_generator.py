from pathlib import Path
import json
import pytest
from proboscis_linter.models import LintViolation
from proboscis_linter.report_generator import TextReportGenerator, JsonReportGenerator


@pytest.mark.unit
def test_text_report_generator_empty():
    generator = TextReportGenerator()
    report = generator.generate_report([])
    
    assert "No violations found" in report
    assert "✓" in report


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
def test_report_generator_names():
    text_gen = TextReportGenerator()
    json_gen = JsonReportGenerator()
    
    assert text_gen.get_format_name() == "text"
    assert json_gen.get_format_name() == "json"


@pytest.mark.unit
def test_text_report_with_mixed_severities():
    """Test text report with different severity levels."""
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("src/critical.py"),
            line_number=5,
            function_name="critical_func",
            message="Missing unit test",
            severity="error"
        ),
        LintViolation(
            rule_name="PL002:require-integration-test",
            file_path=Path("src/utils.py"),
            line_number=15,
            function_name="helper_func",
            message="Missing integration test",
            severity="warning"
        )
    ]
    
    generator = TextReportGenerator()
    report = generator.generate_report(violations)
    
    assert "ERROR:" in report
    assert "WARNING:" in report
    assert "critical.py:5" in report
    assert "utils.py:15" in report
    assert "Total violations: 2" in report


@pytest.mark.unit
def test_text_report_tip_section():
    """Test that text report includes helpful tips."""
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("src/module.py"),
            line_number=10,
            function_name="my_func",
            message="Missing unit test",
            severity="error"
        )
    ]
    
    generator = TextReportGenerator()
    report = generator.generate_report(violations)
    
    # Should include tip about noqa comments
    assert "Tip:" in report
    assert "#noqa" in report
    assert "PL001" in report
    assert "def special_function():  #noqa PL001" in report
    assert "def another_function():  #noqa PL001, PL002" in report


@pytest.mark.unit
def test_json_report_empty():
    """Test JSON report with no violations."""
    generator = JsonReportGenerator()
    report = generator.generate_report([])
    
    data = json.loads(report)
    assert data["total_violations"] == 0
    assert data["violations"] == []
    assert isinstance(data["violations"], list)


@pytest.mark.unit
def test_json_report_multiple_violations():
    """Test JSON report with multiple violations."""
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("/project/src/module1.py"),
            line_number=10,
            function_name="func1",
            message="Function 'func1' missing unit test",
            severity="error"
        ),
        LintViolation(
            rule_name="PL002:require-integration-test",
            file_path=Path("/project/src/module2.py"),
            line_number=20,
            function_name="func2",
            message="Function 'func2' missing integration test",
            severity="warning"
        ),
        LintViolation(
            rule_name="PL003:require-e2e-test",
            file_path=Path("/project/src/module3.py"),
            line_number=30,
            function_name="func3",
            message="Function 'func3' missing e2e test",
            severity="error"
        )
    ]
    
    generator = JsonReportGenerator()
    report = generator.generate_report(violations)
    
    data = json.loads(report)
    assert data["total_violations"] == 3
    assert len(data["violations"]) == 3
    
    # Check first violation
    v1 = data["violations"][0]
    assert v1["rule"] == "PL001:require-unit-test"
    assert v1["function"] == "func1"
    assert v1["file"] == "/project/src/module1.py"
    assert v1["line"] == 10
    assert v1["message"] == "Function 'func1' missing unit test"
    assert v1["severity"] == "error"
    
    # Check all violations have required fields
    for violation in data["violations"]:
        assert "rule" in violation
        assert "function" in violation
        assert "file" in violation
        assert "line" in violation
        assert "message" in violation
        assert "severity" in violation


@pytest.mark.unit
def test_json_report_formatting():
    """Test JSON report is properly formatted."""
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("src/test.py"),
            line_number=1,
            function_name="test",
            message="Test message",
            severity="error"
        )
    ]
    
    generator = JsonReportGenerator()
    report = generator.generate_report(violations)
    
    # Should be valid JSON with proper indentation
    data = json.loads(report)
    assert data is not None
    
    # Check indentation (2 spaces)
    assert "  " in report
    assert '{\n  "total_violations"' in report


@pytest.mark.unit
def test_report_generator_with_special_characters():
    """Test report generation with special characters in paths and names."""
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("src/special chars & symbols/module.py"),
            line_number=42,
            function_name="func_with_unicode_αβγ",
            message="Function 'func_with_unicode_αβγ' missing unit test",
            severity="error"
        )
    ]
    
    # Test text report
    text_gen = TextReportGenerator()
    text_report = text_gen.generate_report(violations)
    assert "special chars & symbols" in text_report
    assert "func_with_unicode_αβγ" in text_report
    
    # Test JSON report
    json_gen = JsonReportGenerator()
    json_report = json_gen.generate_report(violations)
    data = json.loads(json_report)  # Should not raise
    assert "special chars & symbols" in data["violations"][0]["file"]
    assert data["violations"][0]["function"] == "func_with_unicode_αβγ"
# Direct test functions expected by the linter
@pytest.mark.unit
def test_TextReportGenerator_generate_report():
    """Test TextReportGenerator.generate_report method."""
    from proboscis_linter.models import LintViolation
    from proboscis_linter.report_generator import TextReportGenerator
    
    generator = TextReportGenerator()
    violations = [
        LintViolation(
            rule_name="PL001:require-test",
            file_path=Path("test.py"),
            line_number=10,
            function_name="test_func",
            message="Missing test",
            severity="error"
        )
    ]
    report = generator.generate_report(violations)
    assert "Found 1 violations" in report
    assert "test_func" in report


@pytest.mark.unit
def test_TextReportGenerator_get_format_name():
    """Test TextReportGenerator.get_format_name method."""
    from proboscis_linter.report_generator import TextReportGenerator
    generator = TextReportGenerator()
    assert generator.get_format_name() == "text"


@pytest.mark.unit
def test_JsonReportGenerator_generate_report():
    """Test JsonReportGenerator.generate_report method."""
    from proboscis_linter.models import LintViolation
    from proboscis_linter.report_generator import JsonReportGenerator
    import json
    
    generator = JsonReportGenerator()
    violations = [
        LintViolation(
            rule_name="PL001:require-test",
            file_path=Path("test.py"),
            line_number=10,
            function_name="test_func",
            message="Missing test",
            severity="error"
        )
    ]
    report = generator.generate_report(violations)
    data = json.loads(report)
    assert data["total_violations"] == 1
    assert len(data["violations"]) == 1


@pytest.mark.unit
def test_JsonReportGenerator_get_format_name():
    """Test JsonReportGenerator.get_format_name method."""
    from proboscis_linter.report_generator import JsonReportGenerator
    generator = JsonReportGenerator()
    assert generator.get_format_name() == "json"