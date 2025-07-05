"""Tests for configuration module."""
from pathlib import Path
import tempfile
import pytest
from proboscis_linter.config import ProboscisConfig, ConfigLoader, RuleConfig


def test_default_config():
    """Test default configuration values."""
    config = ProboscisConfig()
    
    assert config.test_directories == ["test", "tests"]
    assert config.test_patterns == ["test_*.py", "*_test.py"]
    assert config.exclude_patterns == []
    assert config.output_format == "text"
    assert config.fail_on_error is False
    assert config.rules == {}


def test_config_validation():
    """Test configuration validation."""
    # Valid config
    config = ProboscisConfig(
        test_directories=["tests"],
        output_format="json",
        fail_on_error=True
    )
    assert config.test_directories == ["tests"]
    assert config.output_format == "json"
    
    # Invalid output format
    with pytest.raises(ValueError, match="Invalid output format"):
        ProboscisConfig(output_format="yaml")
    
    # Empty test directories
    with pytest.raises(ValueError, match="List cannot be empty"):
        ProboscisConfig(test_directories=[])


def test_rule_config():
    """Test rule configuration."""
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False, options={"severity": "warning"})
        }
    )
    
    assert config.is_rule_enabled("PL001") is True
    assert config.is_rule_enabled("PL002") is False
    assert config.is_rule_enabled("PL003") is True  # Default
    
    assert config.get_rule_options("PL001") == {}
    assert config.get_rule_options("PL002") == {"severity": "warning"}
    assert config.get_rule_options("PL003") == {}


def test_load_from_pyproject_toml(tmp_path):
    """Test loading configuration from pyproject.toml."""
    config_content = """
[tool.proboscis]
test_directories = ["tests", "test"]
test_patterns = ["test_*.py", "*_spec.py"]
exclude_patterns = ["**/migrations/**"]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = false
"""
    
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(config_content)
    
    config = ConfigLoader.load_from_file(config_file)
    
    assert config.test_directories == ["tests", "test"]
    assert config.test_patterns == ["test_*.py", "*_spec.py"]
    assert config.exclude_patterns == ["**/migrations/**"]
    assert config.output_format == "json"
    assert config.fail_on_error is True
    assert config.is_rule_enabled("PL001") is True
    assert config.is_rule_enabled("PL002") is False


def test_load_from_pyproject_toml_with_detailed_rules(tmp_path):
    """Test loading configuration with detailed rule configuration."""
    config_content = """
[tool.proboscis]
test_directories = ["tests"]

[tool.proboscis.rules.PL001]
enabled = true
options = {max_violations = 10}

[tool.proboscis.rules.PL002]
enabled = false
"""
    
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(config_content)
    
    config = ConfigLoader.load_from_file(config_file)
    
    assert config.is_rule_enabled("PL001") is True
    assert config.get_rule_options("PL001") == {"max_violations": 10}
    assert config.is_rule_enabled("PL002") is False


def test_load_missing_file():
    """Test loading from non-existent file."""
    config = ConfigLoader.load_from_file(Path("non_existent.toml"))
    
    # Should return default config
    assert config.test_directories == ["test", "tests"]
    assert config.output_format == "text"


def test_find_config_file(tmp_path):
    """Test finding config file in directory hierarchy."""
    # Create nested directory structure
    project_root = tmp_path / "project"
    subdir = project_root / "src" / "module"
    subdir.mkdir(parents=True)
    
    # Create config file at project root
    config_content = """
[tool.proboscis]
test_directories = ["spec"]
"""
    config_file = project_root / "pyproject.toml"
    config_file.write_text(config_content)
    
    # Should find config from subdirectory
    found = ConfigLoader.find_config_file(subdir)
    assert found == config_file
    
    # Should not find config without [tool.proboscis] section
    config_file.write_text("[tool.other]\nvalue = 1")
    found = ConfigLoader.find_config_file(subdir)
    assert found is None


def test_merge_cli_options():
    """Test merging CLI options with configuration."""
    config = ProboscisConfig(
        output_format="text",
        fail_on_error=False,
        exclude_patterns=["*.pyc"]
    )
    
    merged = ConfigLoader.merge_cli_options(
        config,
        format="json",
        fail_on_error=True,
        exclude=["*.tmp", "*.log"]
    )
    
    assert merged.output_format == "json"
    assert merged.fail_on_error is True
    assert merged.exclude_patterns == ["*.pyc", "*.tmp", "*.log"]
    
    # Test with None values (no override)
    merged2 = ConfigLoader.merge_cli_options(
        config,
        format=None,
        fail_on_error=None,
        exclude=None
    )
    
    assert merged2.output_format == "text"
    assert merged2.fail_on_error is False
    assert merged2.exclude_patterns == ["*.pyc"]