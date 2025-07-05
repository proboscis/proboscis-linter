"""Integration tests for config module."""
import tempfile
from pathlib import Path
from proboscis_linter.config import ProboscisConfig, ConfigLoader, RuleConfig


@pytest.mark.integration
def test_ProboscisConfig_validate_output_format():
    """Integration test for ProboscisConfig.validate_output_format method."""
    # Test valid formats
    assert ProboscisConfig.validate_output_format("text") == "text"
    assert ProboscisConfig.validate_output_format("json") == "json"
    
    # Test invalid format raises ValueError
    import pytest
    with pytest.raises(ValueError, match="Invalid output format"):
        ProboscisConfig.validate_output_format("xml")
    
    with pytest.raises(ValueError, match="Invalid output format"):
        ProboscisConfig.validate_output_format("yaml")


@pytest.mark.integration
def test_ProboscisConfig_validate_non_empty_list():
    """Integration test for ProboscisConfig.validate_non_empty_list method."""
    # Test valid lists
    assert ProboscisConfig.validate_non_empty_list(["test"]) == ["test"]
    assert ProboscisConfig.validate_non_empty_list(["a", "b", "c"]) == ["a", "b", "c"]
    
    # Test empty list raises ValueError
    import pytest
    with pytest.raises(ValueError, match="List cannot be empty"):
        ProboscisConfig.validate_non_empty_list([])


@pytest.mark.integration
def test_ProboscisConfig_is_rule_enabled():
    """Integration test for ProboscisConfig.is_rule_enabled method."""
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False),
            "PL003": RuleConfig(enabled=True, options={"strict": True}),
        }
    )
    
    # Test configured rules
    assert config.is_rule_enabled("PL001") is True
    assert config.is_rule_enabled("PL002") is False
    assert config.is_rule_enabled("PL003") is True
    
    # Test unconfigured rule defaults to True
    assert config.is_rule_enabled("PL999") is True
    assert config.is_rule_enabled("NEW_RULE") is True


@pytest.mark.integration
def test_ProboscisConfig_get_rule_options():
    """Integration test for ProboscisConfig.get_rule_options method."""
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=True, options={"severity": "warning"}),
            "PL003": RuleConfig(
                enabled=False,
                options={"ignore_private": True, "max_violations": 10}
            ),
        }
    )
    
    # Test rules with no options
    assert config.get_rule_options("PL001") == {}
    
    # Test rules with options
    assert config.get_rule_options("PL002") == {"severity": "warning"}
    assert config.get_rule_options("PL003") == {"ignore_private": True, "max_violations": 10}
    
    # Test unconfigured rule returns empty dict
    assert config.get_rule_options("PL999") == {}
    assert config.get_rule_options("UNKNOWN") == {}


@pytest.mark.integration
def test_ConfigLoader_load_from_file():
    """Integration test for ConfigLoader.load_from_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        config_file = tmppath / "pyproject.toml"
        
        # Create a valid config file
        config_file.write_text("""
[tool.proboscis]
test_directories = ["custom_tests"]
test_patterns = ["check_*.py"]
exclude_patterns = ["*.tmp"]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = false
""")
        
        # Load configuration
        config = ConfigLoader.load_from_file(config_file)
        
        # Verify loaded values
        assert config.test_directories == ["custom_tests"]
        assert config.test_patterns == ["check_*.py"]
        assert config.exclude_patterns == ["*.tmp"]
        assert config.output_format == "json"
        assert config.fail_on_error is True
        assert config.is_rule_enabled("PL001") is True
        assert config.is_rule_enabled("PL002") is False


@pytest.mark.integration
def test_ConfigLoader_find_config_file():
    """Integration test for ConfigLoader.find_config_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create nested directory structure
        deep_path = tmppath / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        
        # No config file exists
        assert ConfigLoader.find_config_file(deep_path) is None
        
        # Add config at level b
        config_b = tmppath / "a" / "b" / "pyproject.toml"
        config_b.write_text("[tool.proboscis]\n")
        
        # Should find config from deep path
        assert ConfigLoader.find_config_file(deep_path) == config_b
        
        # Should find config from b itself
        assert ConfigLoader.find_config_file(tmppath / "a" / "b") == config_b
        
        # Should not find from parent of b
        assert ConfigLoader.find_config_file(tmppath / "a") is None


@pytest.mark.integration
def test_ConfigLoader_merge_cli_options():
    """Integration test for ConfigLoader.merge_cli_options method."""
    # Create base config
    base_config = ProboscisConfig(
        test_directories=["tests"],
        test_patterns=["test_*.py"],
        exclude_patterns=["*.pyc"],
        output_format="text",
        fail_on_error=False
    )
    
    # Test merging with various CLI options
    merged = ConfigLoader.merge_cli_options(
        base_config,
        format="json",
        fail_on_error=True,
        exclude=["*.tmp", "*.cache"]
    )
    
    # Verify merged values
    assert merged.output_format == "json"  # Overridden
    assert merged.fail_on_error is True  # Overridden
    assert merged.exclude_patterns == ["*.pyc", "*.tmp", "*.cache"]  # Extended
    
    # Verify unchanged values
    assert merged.test_directories == ["tests"]
    assert merged.test_patterns == ["test_*.py"]
    
    # Test with None values (no override)
    merged2 = ConfigLoader.merge_cli_options(
        base_config,
        format=None,
        fail_on_error=None,
        exclude=None
    )
    
    # Should keep original values
    assert merged2.output_format == "text"
    assert merged2.fail_on_error is False
    assert merged2.exclude_patterns == ["*.pyc"]


class TestConfigIntegration:
    """Integration tests for configuration loading and management."""
    
    @pytest.mark.integration
    def test_load_complex_config_file(self):
        """Test loading a complex configuration file with all features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            config_file = tmppath / "pyproject.toml"
            
            # Create a comprehensive config file
            config_content = """
[tool.proboscis]
test_directories = ["tests", "spec", "test"]
test_patterns = ["test_*.py", "*_test.py", "*_spec.py"]
exclude_patterns = ["**/vendor/**", "**/node_modules/**", "**/__pycache__/**", "*.pyc"]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = false

[tool.proboscis.rules.PL003]
enabled = true
options = {severity = "warning", max_violations = 10}

[tool.proboscis.rules.PL004]
enabled = false
options = {ignore_private = true}

# Other tool configurations
[tool.black]
line-length = 88

[build-system]
requires = ["setuptools", "wheel"]
"""
            config_file.write_text(config_content)
            
            # Load configuration
            config = ConfigLoader.load_from_file(config_file)
            
            # Verify all settings are loaded correctly
            assert config.test_directories == ["tests", "spec", "test"]
            assert config.test_patterns == ["test_*.py", "*_test.py", "*_spec.py"]
            assert config.exclude_patterns == ["**/vendor/**", "**/node_modules/**", "**/__pycache__/**", "*.pyc"]
            assert config.output_format == "json"
            assert config.fail_on_error is True
            
            # Verify rule configurations
            assert config.is_rule_enabled("PL001") is True
            assert config.is_rule_enabled("PL002") is False
            assert config.is_rule_enabled("PL003") is True
            assert config.is_rule_enabled("PL004") is False
            
            # Verify rule options
            assert config.get_rule_options("PL001") == {}
            assert config.get_rule_options("PL002") == {}
            assert config.get_rule_options("PL003") == {"severity": "warning", "max_violations": 10}
            assert config.get_rule_options("PL004") == {"ignore_private": True}
    
    @pytest.mark.integration
    def test_config_inheritance_hierarchy(self):
        """Test configuration inheritance in nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create directory structure
            root = tmppath / "project"
            subproject = root / "subproject"
            module = subproject / "module"
            module.mkdir(parents=True)
            
            # Root config
            root_config = root / "pyproject.toml"
            root_config.write_text("""
[tool.proboscis]
test_directories = ["tests"]
output_format = "text"

[tool.proboscis.rules]
PL001 = true
PL002 = true
""")
            
            # Subproject config (overrides some settings)
            sub_config = subproject / "pyproject.toml"
            sub_config.write_text("""
[tool.proboscis]
test_directories = ["spec"]
output_format = "json"

[tool.proboscis.rules]
PL002 = false
PL003 = true
""")
            
            # Test finding config from different levels
            # From module dir, should find subproject config
            found = ConfigLoader.find_config_file(module)
            assert found == sub_config
            
            config = ConfigLoader.load_from_file(found)
            assert config.test_directories == ["spec"]
            assert config.output_format == "json"
            
            # From subproject dir, should find subproject config
            found = ConfigLoader.find_config_file(subproject)
            assert found == sub_config
            
            # From root dir, should find root config
            found = ConfigLoader.find_config_file(root)
            assert found == root_config
            
            config = ConfigLoader.load_from_file(found)
            assert config.test_directories == ["tests"]
            assert config.output_format == "text"
    
    @pytest.mark.integration
    def test_cli_override_integration(self):
        """Test CLI options overriding file configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            config_file = tmppath / "pyproject.toml"
            
            # Create config file
            config_file.write_text("""
[tool.proboscis]
test_directories = ["tests"]
test_patterns = ["test_*.py"]
exclude_patterns = ["*.pyc", "*.pyo"]
output_format = "text"
fail_on_error = false

[tool.proboscis.rules]
PL001 = true
PL002 = false
""")
            
            # Load base configuration
            base_config = ConfigLoader.load_from_file(config_file)
            
            # Apply CLI overrides
            cli_config = ConfigLoader.merge_cli_options(
                base_config,
                format="json",
                fail_on_error=True,
                exclude=["*.tmp", "*.cache"]
            )
            
            # Verify overrides
            assert cli_config.output_format == "json"  # Overridden
            assert cli_config.fail_on_error is True  # Overridden
            assert cli_config.exclude_patterns == ["*.pyc", "*.pyo", "*.tmp", "*.cache"]  # Extended
            
            # Verify non-overridden values remain
            assert cli_config.test_directories == ["tests"]
            assert cli_config.test_patterns == ["test_*.py"]
            assert cli_config.is_rule_enabled("PL001") is True
            assert cli_config.is_rule_enabled("PL002") is False
    
    @pytest.mark.integration
    def test_config_validation_integration(self):
        """Test configuration validation with various invalid configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            config_file = tmppath / "pyproject.toml"
            
            # Test 1: Invalid output format
            config_file.write_text("""
[tool.proboscis]
output_format = "xml"
""")
            # Should fall back to default config due to validation error
            config = ConfigLoader.load_from_file(config_file)
            assert config.output_format == "text"  # Default
            
            # Test 2: Empty test directories
            config_file.write_text("""
[tool.proboscis]
test_directories = []
""")
            config = ConfigLoader.load_from_file(config_file)
            assert config.test_directories == ["test", "tests"]  # Default
            
            # Test 3: Invalid rule configuration
            config_file.write_text("""
[tool.proboscis]
test_directories = ["tests"]

[tool.proboscis.rules]
PL001 = "invalid"
""")
            config = ConfigLoader.load_from_file(config_file)
            # Should handle gracefully and use defaults
            assert config.is_rule_enabled("PL001") is True  # Default
    
    @pytest.mark.integration
    def test_missing_config_fallback(self):
        """Test behavior when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # No config file exists
            found = ConfigLoader.find_config_file(tmppath)
            assert found is None
            
            # Loading non-existent file returns defaults
            config = ConfigLoader.load_from_file(tmppath / "nonexistent.toml")
            assert config == ProboscisConfig()  # Default config
            
            # All defaults should be set
            assert config.test_directories == ["test", "tests"]
            assert config.test_patterns == ["test_*.py", "*_test.py"]
            assert config.exclude_patterns == []
            assert config.output_format == "text"
            assert config.fail_on_error is False
            assert config.rules == {}
    
    @pytest.mark.integration
    def test_config_with_environment_variables(self):
        """Test configuration interaction with environment settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create multiple config files to test precedence
            project_root = tmppath / "workspace" / "project"
            project_root.mkdir(parents=True)
            
            # Workspace level config
            workspace_config = tmppath / "workspace" / "pyproject.toml"
            workspace_config.write_text("""
[tool.proboscis]
test_directories = ["workspace_tests"]
output_format = "text"
""")
            
            # Project level config
            project_config = project_root / "pyproject.toml"
            project_config.write_text("""
[tool.proboscis]
test_directories = ["project_tests"]
output_format = "json"

[tool.proboscis.rules]
PL001 = false
""")
            
            # Should find project config when starting from project
            found = ConfigLoader.find_config_file(project_root)
            assert found == project_config
            
            config = ConfigLoader.load_from_file(found)
            assert config.test_directories == ["project_tests"]
            assert config.output_format == "json"
            assert config.is_rule_enabled("PL001") is False
    
    @pytest.mark.integration
    def test_rule_configuration_combinations(self):
        """Test various rule configuration combinations."""
        config = ProboscisConfig(
            rules={
                # Boolean style
                "PL001": RuleConfig(enabled=True),
                "PL002": RuleConfig(enabled=False),
                # With options
                "PL003": RuleConfig(enabled=True, options={"strict": True, "threshold": 5}),
                "PL004": RuleConfig(enabled=False, options={"ignore_tests": True}),
                # Complex options
                "PL005": RuleConfig(
                    enabled=True,
                    options={
                        "include_patterns": ["*.py", "*.pyx"],
                        "exclude_patterns": ["*_pb2.py"],
                        "severity_overrides": {"warning": ["test_*", "*_test"]}
                    }
                )
            }
        )
        
        # Test rule states
        assert config.is_rule_enabled("PL001") is True
        assert config.is_rule_enabled("PL002") is False
        assert config.is_rule_enabled("PL003") is True
        assert config.is_rule_enabled("PL004") is False
        assert config.is_rule_enabled("PL005") is True
        assert config.is_rule_enabled("PL999") is True  # Not configured, default enabled
        
        # Test rule options
        assert config.get_rule_options("PL001") == {}
        assert config.get_rule_options("PL002") == {}
        assert config.get_rule_options("PL003") == {"strict": True, "threshold": 5}
        assert config.get_rule_options("PL004") == {"ignore_tests": True}
        assert config.get_rule_options("PL005") == {
            "include_patterns": ["*.py", "*.pyx"],
            "exclude_patterns": ["*_pb2.py"],
            "severity_overrides": {"warning": ["test_*", "*_test"]}
        }
        assert config.get_rule_options("PL999") == {}  # Not configured