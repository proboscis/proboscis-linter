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


def test_validate_output_format():
    """Test validate_output_format validator."""
    # Valid formats
    assert ProboscisConfig.validate_output_format("text") == "text"
    assert ProboscisConfig.validate_output_format("json") == "json"
    
    # Invalid format
    with pytest.raises(ValueError, match="Invalid output format: xml"):
        ProboscisConfig.validate_output_format("xml")
    
    with pytest.raises(ValueError, match="Invalid output format: yaml"):
        ProboscisConfig.validate_output_format("yaml")


def test_validate_non_empty_list():
    """Test validate_non_empty_list validator."""
    # Valid non-empty lists
    assert ProboscisConfig.validate_non_empty_list(["test"]) == ["test"]
    assert ProboscisConfig.validate_non_empty_list(["test", "tests"]) == ["test", "tests"]
    
    # Empty list should raise error
    with pytest.raises(ValueError, match="List cannot be empty"):
        ProboscisConfig.validate_non_empty_list([])


def test_is_rule_enabled():
    """Test is_rule_enabled method."""
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False),
            "PL003": RuleConfig(enabled=True, options={"strict": True})
        }
    )
    
    # Explicitly enabled rules
    assert config.is_rule_enabled("PL001") is True
    assert config.is_rule_enabled("PL003") is True
    
    # Explicitly disabled rule
    assert config.is_rule_enabled("PL002") is False
    
    # Rule not in config (defaults to enabled)
    assert config.is_rule_enabled("PL004") is True
    assert config.is_rule_enabled("PL999") is True


def test_get_rule_options():
    """Test get_rule_options method."""
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False, options={"severity": "warning"}),
            "PL003": RuleConfig(enabled=True, options={"strict": True, "max_violations": 5})
        }
    )
    
    # Rule with no options
    assert config.get_rule_options("PL001") == {}
    
    # Rule with options
    assert config.get_rule_options("PL002") == {"severity": "warning"}
    assert config.get_rule_options("PL003") == {"strict": True, "max_violations": 5}
    
    # Rule not in config
    assert config.get_rule_options("PL004") == {}
    assert config.get_rule_options("PL999") == {}


def test_load_from_file():
    """Test load_from_file with various scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Test 1: Valid config file
        config_file = tmppath / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
test_directories = ["spec"]
output_format = "json"
""")
        config = ConfigLoader.load_from_file(config_file)
        assert config.test_directories == ["spec"]
        assert config.output_format == "json"
        
        # Test 2: Invalid TOML
        config_file.write_text("invalid toml content [[[")
        config = ConfigLoader.load_from_file(config_file)
        # Should return default config on error
        assert config.test_directories == ["test", "tests"]
        
        # Test 3: TOML without [tool.proboscis] section
        config_file.write_text("""
[build-system]
requires = ["setuptools"]
""")
        config = ConfigLoader.load_from_file(config_file)
        # Should return default config
        assert config.test_directories == ["test", "tests"]


def test_find_config_file():
    """Test find_config_file traversing directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create nested directory structure
        root = tmppath / "project"
        sub1 = root / "src"
        sub2 = sub1 / "module"
        sub3 = sub2 / "submodule"
        sub3.mkdir(parents=True)
        
        # No config file exists
        assert ConfigLoader.find_config_file(sub3) is None
        
        # Config at root level
        config_file = root / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
test_directories = ["test"]
""")
        assert ConfigLoader.find_config_file(sub3) == config_file
        assert ConfigLoader.find_config_file(sub2) == config_file
        assert ConfigLoader.find_config_file(sub1) == config_file
        assert ConfigLoader.find_config_file(root) == config_file
        
        # Config without [tool.proboscis] should be ignored
        config_file.write_text("""
[tool.other]
value = 1
""")
        assert ConfigLoader.find_config_file(sub3) is None
        
        # Multiple config files - should find the closest one
        sub1_config = sub1 / "pyproject.toml"
        sub1_config.write_text("""
[tool.proboscis]
test_directories = ["spec"]
""")
        assert ConfigLoader.find_config_file(sub3) == sub1_config
        assert ConfigLoader.find_config_file(sub2) == sub1_config
        assert ConfigLoader.find_config_file(sub1) == sub1_config


def test_merge_cli_options():
    """Test merge_cli_options with various option combinations."""
    base_config = ProboscisConfig(
        test_directories=["test"],
        test_patterns=["test_*.py"],
        exclude_patterns=["*.pyc"],
        output_format="text",
        fail_on_error=False
    )
    
    # Test overriding format
    merged = ConfigLoader.merge_cli_options(base_config, format="json")
    assert merged.output_format == "json"
    assert merged.test_directories == ["test"]  # Unchanged
    
    # Test overriding fail_on_error
    merged = ConfigLoader.merge_cli_options(base_config, fail_on_error=True)
    assert merged.fail_on_error is True
    assert merged.output_format == "text"  # Unchanged
    
    # Test extending exclude patterns
    merged = ConfigLoader.merge_cli_options(base_config, exclude=["*.tmp", "*.log"])
    assert merged.exclude_patterns == ["*.pyc", "*.tmp", "*.log"]
    
    # Test all options together
    merged = ConfigLoader.merge_cli_options(
        base_config,
        format="json",
        fail_on_error=True,
        exclude=["*.bak"]
    )
    assert merged.output_format == "json"
    assert merged.fail_on_error is True
    assert merged.exclude_patterns == ["*.pyc", "*.bak"]
    
    # Test with empty/None options (no changes)
    merged = ConfigLoader.merge_cli_options(base_config)
    assert merged.output_format == "text"
    assert merged.fail_on_error is False
    assert merged.exclude_patterns == ["*.pyc"]