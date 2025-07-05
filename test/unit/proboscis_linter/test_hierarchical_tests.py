"""Test hierarchical test discovery (unit/integration/e2e)."""
import pytest
from pathlib import Path
from proboscis_linter.rust_linter import RustLinterWrapper
from proboscis_linter.config import ProboscisConfig, RuleConfig


class TestHierarchicalTests:
    """Test the hierarchical test structure support."""
    
    def test_unit_test_discovery(self):
        """Test that PL001 finds unit tests in test/unit/ directory."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = RustLinterWrapper(config)
        
        test_project = Path(__file__).parent.parent.parent / "fixtures" / "test_project_hierarchical"
        violations = linter.lint_project(test_project)
        
        # Filter for PL001 violations
        pl001_violations = [v for v in violations if v.rule_name.startswith("PL001")]
        
        # Should find violations for:
        # - divide (no unit test)
        # - calculate_total (no unit test)
        assert len(pl001_violations) == 2
        
        function_names = {v.function_name for v in pl001_violations}
        assert function_names == {"divide", "calculate_total"}
    
    def test_integration_test_discovery(self):
        """Test that PL002 finds integration tests in test/integration/ directory."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=False),
                "PL002": RuleConfig(enabled=True),
                "PL003": RuleConfig(enabled=False)
            }
        )
        linter = RustLinterWrapper(config)
        
        test_project = Path(__file__).parent.parent.parent / "fixtures" / "test_project_hierarchical"
        violations = linter.lint_project(test_project)
        
        # Filter for PL002 violations
        pl002_violations = [v for v in violations if v.rule_name.startswith("PL002")]
        
        # Should find violations for:
        # - add (no integration test)
        # - multiply (no integration test)
        # - calculate_total (no integration test)
        assert len(pl002_violations) == 3
        
        function_names = {v.function_name for v in pl002_violations}
        assert function_names == {"add", "multiply", "calculate_total"}
    
    def test_e2e_test_discovery(self):
        """Test that PL003 finds e2e tests in test/e2e/ directory."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=False),
                "PL002": RuleConfig(enabled=False),
                "PL003": RuleConfig(enabled=True)
            }
        )
        linter = RustLinterWrapper(config)
        
        test_project = Path(__file__).parent.parent.parent / "fixtures" / "test_project_hierarchical"
        violations = linter.lint_project(test_project)
        
        # Filter for PL003 violations
        pl003_violations = [v for v in violations if v.rule_name.startswith("PL003")]
        
        # Should find violations for:
        # - add (no e2e test)
        # - multiply (no e2e test)
        # - divide (no e2e test)
        assert len(pl003_violations) == 3
        
        function_names = {v.function_name for v in pl003_violations}
        assert function_names == {"add", "multiply", "divide"}
    
    def test_all_rules_together(self):
        """Test all three rules running together."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=True),
                "PL003": RuleConfig(enabled=True)
            }
        )
        linter = RustLinterWrapper(config)
        
        test_project = Path(__file__).parent.parent.parent / "fixtures" / "test_project_hierarchical"
        violations = linter.lint_project(test_project)
        
        # Count violations by rule
        rule_counts = {}
        for v in violations:
            rule_id = v.rule_name.split(":")[0]
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        
        # Should have violations from all three rules
        assert "PL001" in rule_counts
        assert "PL002" in rule_counts
        assert "PL003" in rule_counts
        
        # Total should be 8 (as we saw in manual test)
        assert sum(rule_counts.values()) == 8
    
    def test_error_messages_show_correct_directories(self):
        """Test that error messages indicate the correct test directory."""
        config = ProboscisConfig(
            test_directories=["test"],
            rules={
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=True),
                "PL003": RuleConfig(enabled=True)
            }
        )
        linter = RustLinterWrapper(config)
        
        test_project = Path(__file__).parent.parent.parent / "fixtures" / "test_project_hierarchical"
        violations = linter.lint_project(test_project)
        
        # Check that each rule mentions the correct directory
        for v in violations:
            if v.rule_name.startswith("PL001"):
                assert "test/unit/" in v.message
            elif v.rule_name.startswith("PL002"):
                assert "test/integration/" in v.message
            elif v.rule_name.startswith("PL003"):
                assert "test/e2e/" in v.message