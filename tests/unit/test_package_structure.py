"""Test package structure enforcement and class method detection."""
from pathlib import Path
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig, RuleConfig


class TestPackageStructure:
    """Test that the linter enforces test organization matching source structure."""
    
    def test_class_method_detection(self):
        """Test that class methods are detected and reported differently from functions."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = ProboscisLinter(config)
        
        test_project = Path(__file__).parent.parent / "fixtures" / "test_project_structured"
        violations = linter.lint_project(test_project)
        
        # Filter for PL001 violations
        pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
        
        # We should have violations for:
        # - Calculator.update (no test)
        # - DataProcessor.update (no test)
        # Total: 2 violations
        assert len(pl001_violations) == 2
        
        # Check that violations mention the class name
        for v in pl001_violations:
            if v.function_name == "update":
                # Should mention it's a method, not just a function
                assert "Method" in v.message or "Calculator" in v.message or "DataProcessor" in v.message
    
    def test_module_path_in_error_messages(self):
        """Test that error messages include the module path in the expected file path."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = ProboscisLinter(config)
        
        test_project = Path(__file__).parent.parent / "fixtures" / "test_project_structured"
        violations = linter.lint_project(test_project)
        
        # All violations should show the module path structure in the expected test file path
        for v in violations:
            assert "/test/unit/pkg/mod1/test_submod.py" in v.message
            
    def test_expected_test_location(self):
        """Test that error messages show the correct expected test location."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = ProboscisLinter(config)
        
        test_project = Path(__file__).parent.parent / "fixtures" / "test_project_structured"
        violations = linter.lint_project(test_project)
        
        # All violations should mention the expected test location as absolute path
        for v in violations:
            # The absolute path should contain the expected structure
            assert "/test/unit/pkg/mod1/test_submod.py" in v.message
            
    def test_class_method_test_patterns(self):
        """Test that the expected test patterns for class methods include the class name."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = ProboscisLinter(config)
        
        test_project = Path(__file__).parent.parent / "fixtures" / "test_project_structured"
        violations = linter.lint_project(test_project)
        
        # Find violations for Calculator.update
        calc_update_violations = [v for v in violations 
                                  if v.function_name == "update" and v.line_number == 22]
        
        assert len(calc_update_violations) == 1
        violation = calc_update_violations[0]
        
        # Should suggest the canonical pattern test_Calculator_update
        assert "test_Calculator_update" in violation.message