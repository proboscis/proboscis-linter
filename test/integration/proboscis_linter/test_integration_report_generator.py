"""Integration tests for report generator module."""
from pathlib import Path
import json
import pytest
from proboscis_linter.models import LintViolation
from proboscis_linter.report_generator import TextReportGenerator, JsonReportGenerator


def test_TextReportGenerator_generate_report():
    """Integration test for TextReportGenerator.generate_report method."""
    generator = TextReportGenerator()
    violations = [
        LintViolation(
            rule_name="PL001:require-unit-test",
            file_path=Path("/test/file.py"),
            line_number=10,
            function_name="test_func",
            message="Missing unit test",
            severity="error"
        )
    ]
    
    report = generator.generate_report(violations)
    assert isinstance(report, str)
    assert "Found 1 violation" in report
    assert "PL001" in report
    assert "test_func" in report


def test_TextReportGenerator_get_format_name():
    """Integration test for TextReportGenerator.get_format_name method."""
    generator = TextReportGenerator()
    assert generator.get_format_name() == "text"


def test_JsonReportGenerator_generate_report():
    """Integration test for JsonReportGenerator.generate_report method."""
    generator = JsonReportGenerator()
    violations = [
        LintViolation(
            rule_name="PL002:require-integration-test",
            file_path=Path("/test/file.py"),
            line_number=20,
            function_name="test_func",
            message="Missing integration test",
            severity="error"
        )
    ]
    
    report = generator.generate_report(violations)
    assert isinstance(report, str)
    
    # Parse JSON to validate
    data = json.loads(report)
    assert data["total_violations"] == 1
    assert len(data["violations"]) == 1
    assert data["violations"][0]["rule_name"] == "PL002:require-integration-test"


def test_JsonReportGenerator_get_format_name():
    """Integration test for JsonReportGenerator.get_format_name method."""
    generator = JsonReportGenerator()
    assert generator.get_format_name() == "json"


class TestReportGeneratorIntegration:
    """Integration tests for report generators."""
    
    @pytest.fixture
    def complex_violations(self):
        """Create a complex set of violations for testing."""
        return [
            # Multiple violations in same file
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("/project/src/core/auth.py"),
                line_number=25,
                function_name="authenticate",
                message="Function 'authenticate' missing unit test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL002:require-integration-test",
                file_path=Path("/project/src/core/auth.py"),
                line_number=25,
                function_name="authenticate",
                message="Function 'authenticate' missing integration test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL003:require-e2e-test",
                file_path=Path("/project/src/core/auth.py"),
                line_number=25,
                function_name="authenticate",
                message="Function 'authenticate' missing e2e test",
                severity="error"
            ),
            
            # Different file, mixed severities
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("/project/src/utils/helpers.py"),
                line_number=42,
                function_name="format_date",
                message="Function 'format_date' missing unit test",
                severity="warning"
            ),
            
            # Class methods
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("/project/src/models/user.py"),
                line_number=15,
                function_name="User.save",
                message="Method 'User.save' missing unit test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL002:require-integration-test",
                file_path=Path("/project/src/models/user.py"),
                line_number=30,
                function_name="User.delete",
                message="Method 'User.delete' missing integration test",
                severity="error"
            ),
            
            # Long file paths
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("/very/long/path/to/deeply/nested/project/structure/src/components/widgets/advanced/custom_widget.py"),
                line_number=100,
                function_name="render_widget",
                message="Function 'render_widget' missing unit test",
                severity="error"
            )
        ]
    
    def test_text_report_complex_output(self, complex_violations):
        """Test text report with complex violation set."""
        generator = TextReportGenerator()
        report = generator.generate_report(complex_violations)
        
        # Check header
        assert "Found 7 violations:" in report
        
        # Check all files are mentioned
        assert "auth.py" in report
        assert "helpers.py" in report
        assert "user.py" in report
        assert "custom_widget.py" in report
        
        # Check line numbers
        assert ":25" in report
        assert ":42" in report
        assert ":15" in report
        assert ":30" in report
        assert ":100" in report
        
        # Check function names appear
        assert "authenticate" in report
        assert "format_date" in report
        assert "User.save" in report
        assert "User.delete" in report
        assert "render_widget" in report
        
        # Check severities
        assert report.count("ERROR:") == 6
        assert report.count("WARNING:") == 1
        
        # Check footer
        assert "Total violations: 7" in report
        assert "Tip:" in report
    
    def test_json_report_complex_structure(self, complex_violations):
        """Test JSON report with complex violation set."""
        generator = JsonReportGenerator()
        report = generator.generate_report(complex_violations)
        
        data = json.loads(report)
        
        # Check structure
        assert data["total_violations"] == 7
        assert len(data["violations"]) == 7
        
        # Group violations by file
        files = {}
        for v in data["violations"]:
            file_path = v["file"]
            if file_path not in files:
                files[file_path] = []
            files[file_path].append(v)
        
        # Check auth.py has 3 violations
        auth_violations = [v for v in data["violations"] if "auth.py" in v["file"]]
        assert len(auth_violations) == 3
        
        # All auth violations should be for same function
        auth_functions = {v["function"] for v in auth_violations}
        assert auth_functions == {"authenticate"}
        
        # Check different rules
        auth_rules = {v["rule"].split(":")[0] for v in auth_violations}
        assert auth_rules == {"PL001", "PL002", "PL003"}
        
        # Check mixed severities
        severities = {v["severity"] for v in data["violations"]}
        assert severities == {"error", "warning"}
    
    def test_report_generation_consistency(self, complex_violations):
        """Test that multiple generations produce consistent results."""
        text_gen = TextReportGenerator()
        json_gen = JsonReportGenerator()
        
        # Generate multiple times
        text_report1 = text_gen.generate_report(complex_violations)
        text_report2 = text_gen.generate_report(complex_violations)
        
        json_report1 = json_gen.generate_report(complex_violations)
        json_report2 = json_gen.generate_report(complex_violations)
        
        # Text reports should be identical
        assert text_report1 == text_report2
        
        # JSON reports should be identical
        assert json_report1 == json_report2
        
        # JSON data should be identical
        data1 = json.loads(json_report1)
        data2 = json.loads(json_report2)
        assert data1 == data2
    
    def test_large_violation_set(self):
        """Test report generation with many violations."""
        # Generate 1000 violations
        violations = []
        for i in range(1000):
            module_idx = i // 10
            func_idx = i % 10
            rule_idx = (i % 3) + 1
            
            violations.append(LintViolation(
                rule_name=f"PL00{rule_idx}:require-test",
                file_path=Path(f"/project/src/module_{module_idx}.py"),
                line_number=10 + func_idx * 5,
                function_name=f"function_{func_idx}",
                message=f"Function 'function_{func_idx}' missing test",
                severity="error" if i % 5 != 0 else "warning"
            ))
        
        # Test text report
        text_gen = TextReportGenerator()
        text_report = text_gen.generate_report(violations)
        
        assert "Found 1000 violations:" in text_report
        assert "Total violations: 1000" in text_report
        
        # Test JSON report
        json_gen = JsonReportGenerator()
        json_report = json_gen.generate_report(violations)
        
        data = json.loads(json_report)
        assert data["total_violations"] == 1000
        assert len(data["violations"]) == 1000
    
    def test_report_ordering(self):
        """Test that violations maintain order in reports."""
        violations = [
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("z_last.py"),
                line_number=1,
                function_name="z_func",
                message="Missing test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("a_first.py"),
                line_number=1,
                function_name="a_func",
                message="Missing test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("m_middle.py"),
                line_number=1,
                function_name="m_func",
                message="Missing test",
                severity="error"
            )
        ]
        
        # Generate reports
        text_gen = TextReportGenerator()
        json_gen = JsonReportGenerator()
        
        text_report = text_gen.generate_report(violations)
        json_report = json_gen.generate_report(violations)
        
        # Check text report maintains order
        z_pos = text_report.find("z_last.py")
        a_pos = text_report.find("a_first.py")
        m_pos = text_report.find("m_middle.py")
        
        assert z_pos < a_pos < m_pos  # Order as given
        
        # Check JSON report maintains order
        data = json.loads(json_report)
        assert data["violations"][0]["file"] == "z_last.py"
        assert data["violations"][1]["file"] == "a_first.py"
        assert data["violations"][2]["file"] == "m_middle.py"
    
    def test_unicode_and_special_paths(self):
        """Test report generation with unicode and special characters."""
        violations = [
            LintViolation(
                rule_name="PL001:require-unit-test",
                file_path=Path("/projekt/źródło/モジュール.py"),
                line_number=42,
                function_name="函数_name",
                message="Function '函数_name' missing unit test",
                severity="error"
            ),
            LintViolation(
                rule_name="PL002:require-integration-test",
                file_path=Path("/path/with spaces/and-dashes/under_scores.py"),
                line_number=100,
                function_name="my-func$special",
                message="Function 'my-func$special' missing integration test",
                severity="warning"
            )
        ]
        
        # Test both generators handle unicode properly
        text_gen = TextReportGenerator()
        json_gen = JsonReportGenerator()
        
        text_report = text_gen.generate_report(violations)
        json_report = json_gen.generate_report(violations)
        
        # Text report should contain unicode
        assert "źródło" in text_report
        assert "モジュール.py" in text_report
        assert "函数_name" in text_report
        
        # JSON should properly encode unicode
        data = json.loads(json_report)
        assert "źródło" in data["violations"][0]["file"]
        assert "函数_name" == data["violations"][0]["function"]
        assert "my-func$special" == data["violations"][1]["function"]
    
    def test_empty_edge_cases(self):
        """Test edge cases with empty or minimal data."""
        # Empty violations
        text_gen = TextReportGenerator()
        json_gen = JsonReportGenerator()
        
        empty_text = text_gen.generate_report([])
        empty_json = json_gen.generate_report([])
        
        assert "No violations found" in empty_text
        assert "✓" in empty_text
        
        data = json.loads(empty_json)
        assert data["total_violations"] == 0
        assert data["violations"] == []
        
        # Single violation with minimal data
        minimal_violation = LintViolation(
            rule_name="PL001",
            file_path=Path("a.py"),
            line_number=1,
            function_name="f",
            message="",
            severity="error"
        )
        
        text_report = text_gen.generate_report([minimal_violation])
        json_report = json_gen.generate_report([minimal_violation])
        
        assert "a.py:1" in text_report
        assert "ERROR:" in text_report
        
        data = json.loads(json_report)
        assert data["violations"][0]["file"] == "a.py"
        assert data["violations"][0]["function"] == "f"