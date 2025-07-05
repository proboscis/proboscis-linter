"""End-to-end tests for config module."""
import tempfile
from pathlib import Path
from proboscis_linter.config import ProboscisConfig, ConfigLoader, RuleConfig


@pytest.mark.e2e
def test_ProboscisConfig_validate_output_format():
    """E2E test for ProboscisConfig.validate_output_format method."""
    # Test valid formats
    assert ProboscisConfig.validate_output_format("text") == "text"
    assert ProboscisConfig.validate_output_format("json") == "json"
    
    # Test invalid format raises ValueError
    import pytest
    with pytest.raises(ValueError, match="Invalid output format"):
        ProboscisConfig.validate_output_format("invalid")


@pytest.mark.e2e
def test_ProboscisConfig_validate_non_empty_list():
    """E2E test for ProboscisConfig.validate_non_empty_list method."""
    # Test with valid data
    assert ProboscisConfig.validate_non_empty_list(["item"]) == ["item"]
    assert ProboscisConfig.validate_non_empty_list(["a", "b"]) == ["a", "b"]
    
    # Test empty list raises ValueError
    import pytest
    with pytest.raises(ValueError, match="List cannot be empty"):
        ProboscisConfig.validate_non_empty_list([])


@pytest.mark.e2e
def test_ProboscisConfig_is_rule_enabled():
    """E2E test for ProboscisConfig.is_rule_enabled method."""
    # Test with various rule configurations
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False),
            "PL003": RuleConfig(enabled=True, options={"strict": True}),
            "PL004": RuleConfig(enabled=False, options={"threshold": 5}),
        }
    )
    
    # Test known rules
    assert config.is_rule_enabled("PL001") is True
    assert config.is_rule_enabled("PL002") is False
    assert config.is_rule_enabled("PL003") is True
    assert config.is_rule_enabled("PL004") is False
    
    # Test unknown rules default to enabled
    assert config.is_rule_enabled("PL999") is True
    assert config.is_rule_enabled("CUSTOM_RULE") is True


@pytest.mark.e2e
def test_ProboscisConfig_get_rule_options():
    """E2E test for ProboscisConfig.get_rule_options method."""
    # Create config with various rule options
    config = ProboscisConfig(
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=True, options={"severity": "error"}),
            "PL003": RuleConfig(
                enabled=True,
                options={
                    "ignore_patterns": ["test_*", "*_test"],
                    "max_violations": 100,
                    "strict_mode": True
                }
            ),
        }
    )
    
    # Test retrieving options
    assert config.get_rule_options("PL001") == {}
    assert config.get_rule_options("PL002") == {"severity": "error"}
    assert config.get_rule_options("PL003") == {
        "ignore_patterns": ["test_*", "*_test"],
        "max_violations": 100,
        "strict_mode": True
    }
    
    # Test unknown rules return empty dict
    assert config.get_rule_options("UNKNOWN") == {}


@pytest.mark.e2e
def test_ConfigLoader_load_from_file():
    """E2E test for ConfigLoader.load_from_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Test with valid config file
        config_file = tmppath / "pyproject.toml"
        config_file.write_text("""
[tool.proboscis]
test_directories = ["spec", "tests"]
test_patterns = ["spec_*.py", "test_*.py"]
exclude_patterns = ["*.generated.py"]
output_format = "json"
fail_on_error = true

[tool.proboscis.rules]
PL001 = false
PL002 = true
PL003 = { enabled = true, options = { severity = "warning" } }
""")
        
        config = ConfigLoader.load_from_file(config_file)
        
        # Verify all settings loaded correctly
        assert config.test_directories == ["spec", "tests"]
        assert config.test_patterns == ["spec_*.py", "test_*.py"]
        assert config.exclude_patterns == ["*.generated.py"]
        assert config.output_format == "json"
        assert config.fail_on_error is True
        assert config.is_rule_enabled("PL001") is False
        assert config.is_rule_enabled("PL002") is True
        assert config.is_rule_enabled("PL003") is True
        assert config.get_rule_options("PL003") == {"severity": "warning"}
        
        # Test with non-existent file
        missing_config = ConfigLoader.load_from_file(tmppath / "missing.toml")
        assert missing_config == ProboscisConfig()  # Should return default


@pytest.mark.e2e
def test_ConfigLoader_find_config_file():
    """E2E test for ConfigLoader.find_config_file method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create directory structure
        root = tmppath / "project"
        sub1 = root / "module1"
        sub2 = root / "module2"
        deep = sub1 / "submodule" / "component"
        deep.mkdir(parents=True)
        sub2.mkdir(parents=True)
        
        # Test when no config exists
        assert ConfigLoader.find_config_file(deep) is None
        
        # Add config at root
        root_config = root / "pyproject.toml"
        root_config.write_text("[tool.proboscis]\n")
        
        # Should find from any subdirectory
        assert ConfigLoader.find_config_file(deep) == root_config
        assert ConfigLoader.find_config_file(sub1) == root_config
        assert ConfigLoader.find_config_file(sub2) == root_config
        assert ConfigLoader.find_config_file(root) == root_config
        
        # Add config in sub1
        sub1_config = sub1 / "pyproject.toml"
        sub1_config.write_text("[tool.proboscis]\n")
        
        # Now deep should find sub1 config instead
        assert ConfigLoader.find_config_file(deep) == sub1_config
        assert ConfigLoader.find_config_file(sub1) == sub1_config
        # But sub2 still finds root config
        assert ConfigLoader.find_config_file(sub2) == root_config


@pytest.mark.e2e
def test_ConfigLoader_merge_cli_options():
    """E2E test for ConfigLoader.merge_cli_options method."""
    # Create base config with specific settings
    base = ProboscisConfig(
        test_directories=["tests"],
        test_patterns=["test_*.py"],
        exclude_patterns=["*.tmp"],
        output_format="text",
        fail_on_error=False,
        rules={
            "PL001": RuleConfig(enabled=True),
            "PL002": RuleConfig(enabled=False),
        }
    )
    
    # Test merging various CLI options
    merged = ConfigLoader.merge_cli_options(
        base,
        format="json",
        fail_on_error=True,
        exclude=["*.cache", "*.log"]
    )
    
    # Check overridden values
    assert merged.output_format == "json"
    assert merged.fail_on_error is True
    assert merged.exclude_patterns == ["*.tmp", "*.cache", "*.log"]
    
    # Check preserved values
    assert merged.test_directories == ["tests"]
    assert merged.test_patterns == ["test_*.py"]
    assert merged.is_rule_enabled("PL001") is True
    assert merged.is_rule_enabled("PL002") is False
    
    # Test partial merge
    partial = ConfigLoader.merge_cli_options(base, format="json")
    assert partial.output_format == "json"
    assert partial.fail_on_error is False  # Not overridden
    assert partial.exclude_patterns == ["*.tmp"]  # Not overridden


class TestConfigE2E:
    """End-to-end tests for configuration in real-world scenarios."""
    
    @pytest.mark.e2e
    def test_multi_project_workspace(self):
        """Test configuration in a multi-project workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Create workspace structure
            # workspace/
            #   pyproject.toml (workspace defaults)
            #   project-a/
            #     pyproject.toml (project specific)
            #     src/
            #   project-b/
            #     src/
            #   project-c/
            #     pyproject.toml (project specific)
            #     lib/
            
            # Workspace config
            workspace_config = workspace / "pyproject.toml"
            workspace_config.write_text("""
[tool.proboscis]
test_directories = ["tests", "test"]
test_patterns = ["test_*.py", "*_test.py"]
output_format = "text"

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false
""")
            
            # Project A - overrides some settings
            project_a = workspace / "project-a"
            project_a_src = project_a / "src"
            project_a_src.mkdir(parents=True)
            
            project_a_config = project_a / "pyproject.toml"
            project_a_config.write_text("""
[tool.proboscis]
test_directories = ["spec", "tests"]
output_format = "json"

[tool.proboscis.rules]
PL002 = false
PL004 = true
""")
            
            # Project B - no config, inherits workspace
            project_b = workspace / "project-b"
            project_b_src = project_b / "src"
            project_b_src.mkdir(parents=True)
            
            # Project C - different config
            project_c = workspace / "project-c"
            project_c_lib = project_c / "lib"
            project_c_lib.mkdir(parents=True)
            
            project_c_config = project_c / "pyproject.toml"
            project_c_config.write_text("""
[tool.proboscis]
test_directories = ["qa"]
exclude_patterns = ["**/generated/**", "**/*_pb2.py"]

[tool.proboscis.rules]
PL001 = false
PL002 = true
PL003 = true
""")
            
            # Test configuration discovery from different locations
            
            # From Project A source
            found = ConfigLoader.find_config_file(project_a_src)
            assert found == project_a_config
            config_a = ConfigLoader.load_from_file(found)
            assert config_a.test_directories == ["spec", "tests"]
            assert config_a.output_format == "json"
            assert config_a.is_rule_enabled("PL001") is True  # From workspace
            assert config_a.is_rule_enabled("PL002") is False  # Overridden
            assert config_a.is_rule_enabled("PL004") is True  # New in project
            
            # From Project B (no local config)
            found = ConfigLoader.find_config_file(project_b_src)
            assert found is None  # No project config, no workspace config found
            
            # From Project C
            found = ConfigLoader.find_config_file(project_c_lib)
            assert found == project_c_config
            config_c = ConfigLoader.load_from_file(found)
            assert config_c.test_directories == ["qa"]
            assert config_c.exclude_patterns == ["**/generated/**", "**/*_pb2.py"]
            assert config_c.is_rule_enabled("PL001") is False
            assert config_c.is_rule_enabled("PL002") is True
            assert config_c.is_rule_enabled("PL003") is True
    
    @pytest.mark.e2e
    def test_real_world_config_scenarios(self):
        """Test configuration handling in real-world scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            # Scenario 1: Django project with custom test structure
            django_config = project / "pyproject.toml"
            django_config.write_text("""
[tool.proboscis]
test_directories = ["tests", "apps/*/tests"]
test_patterns = ["test_*.py", "tests.py"]
exclude_patterns = [
    "**/migrations/**",
    "**/static/**",
    "**/templates/**",
    "manage.py"
]

[tool.proboscis.rules]
# Disable e2e tests for Django apps
PL003 = false

[tool.proboscis.rules.PL001]
enabled = true
options = {skip_management_commands = true}

[tool.django]
settings_module = "myproject.settings"
""")
            
            config = ConfigLoader.load_from_file(django_config)
            assert "apps/*/tests" in config.test_directories
            assert "**/migrations/**" in config.exclude_patterns
            assert config.is_rule_enabled("PL003") is False
            assert config.get_rule_options("PL001") == {"skip_management_commands": True}
            
            # Scenario 2: Monorepo with service-specific configs
            monorepo_root = project / "monorepo"
            monorepo_root.mkdir()
            
            # Root monorepo config
            root_config = monorepo_root / "pyproject.toml"
            root_config.write_text("""
[tool.proboscis]
test_directories = ["test", "tests"]
exclude_patterns = ["**/build/**", "**/dist/**", "**/.tox/**"]

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = true
""")
            
            # Microservice with stricter requirements
            service = monorepo_root / "services" / "auth-service"
            service.mkdir(parents=True)
            
            service_config = service / "pyproject.toml"
            service_config.write_text("""
[tool.proboscis]
test_directories = ["tests/unit", "tests/integration", "tests/e2e"]
test_patterns = ["test_*.py", "*_test.py", "*_spec.py"]
fail_on_error = true

[tool.proboscis.rules]
# All test types required for auth service
PL001 = true
PL002 = true
PL003 = true

[tool.proboscis.rules.PL001]
enabled = true
options = {min_coverage = 90}
""")
            
            config = ConfigLoader.load_from_file(service_config)
            assert "tests/unit" in config.test_directories
            assert "tests/integration" in config.test_directories
            assert "tests/e2e" in config.test_directories
            assert config.fail_on_error is True
            assert config.get_rule_options("PL001") == {"min_coverage": 90}
    
    @pytest.mark.e2e
    def test_config_with_build_tools_integration(self):
        """Test configuration alongside other build tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            # Create a comprehensive pyproject.toml with multiple tools
            config_file = project / "pyproject.toml"
            config_file.write_text("""
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-awesome-project"
version = "1.0.0"
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "ruff>=0.1.0",
    "proboscis-linter>=0.1.0"
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90", "I", "N"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*"]

[tool.proboscis]
test_directories = ["tests"]
test_patterns = ["test_*.py", "*_test.py"]
exclude_patterns = [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/build/**",
    "**/dist/**",
    "**/.pytest_cache/**"
]
output_format = "text"
fail_on_error = true

[tool.proboscis.rules]
PL001 = true
PL002 = true

[tool.proboscis.rules.PL003]
enabled = false
options = {reason = "E2E tests are in separate repo"}

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
""")
            
            # Load and verify proboscis config works alongside other tools
            config = ConfigLoader.load_from_file(config_file)
            
            assert config.test_directories == ["tests"]
            assert config.fail_on_error is True
            assert config.is_rule_enabled("PL001") is True
            assert config.is_rule_enabled("PL002") is True
            assert config.is_rule_enabled("PL003") is False
            assert config.get_rule_options("PL003") == {"reason": "E2E tests are in separate repo"}
    
    @pytest.mark.e2e
    def test_config_migration_scenarios(self):
        """Test configuration migration and compatibility scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            # Scenario: Project with legacy and new config
            config_file = project / "pyproject.toml"
            
            # Start with a minimal config
            config_file.write_text("""
[tool.proboscis]
test_directories = ["test"]
""")
            
            config = ConfigLoader.load_from_file(config_file)
            assert config.test_directories == ["test"]
            # All other settings should have sensible defaults
            assert config.test_patterns == ["test_*.py", "*_test.py"]
            assert config.output_format == "text"
            assert config.fail_on_error is False
            
            # Upgrade to more comprehensive config
            config_file.write_text("""
[tool.proboscis]
# Updated test discovery
test_directories = ["test", "tests", "spec"]
test_patterns = ["test_*.py", "*_test.py", "*_spec.py", "test*.py"]

# New exclusion rules
exclude_patterns = [
    "**/vendor/**",
    "**/third_party/**",
    "**/*_pb2.py",
    "**/*_pb2_grpc.py"
]

# Output settings
output_format = "json"
fail_on_error = true

# Granular rule configuration
[tool.proboscis.rules]
# Keep unit tests mandatory
PL001 = true

# Make integration tests optional for now
[tool.proboscis.rules.PL002]
enabled = false
options = {migration_period = true, target_date = "2024-06-01"}

# E2E tests only for critical paths
[tool.proboscis.rules.PL003]
enabled = true
options = {
    only_for_paths = ["src/api/**", "src/auth/**"],
    skip_utilities = true
}
""")
            
            config = ConfigLoader.load_from_file(config_file)
            
            # Verify migrated configuration
            assert config.test_directories == ["test", "tests", "spec"]
            assert len(config.test_patterns) == 4
            assert "*_spec.py" in config.test_patterns
            assert config.output_format == "json"
            assert config.fail_on_error is True
            
            # Check rule migration
            assert config.is_rule_enabled("PL001") is True
            assert config.is_rule_enabled("PL002") is False
            assert config.get_rule_options("PL002") == {
                "migration_period": True,
                "target_date": "2024-06-01"
            }
            assert config.is_rule_enabled("PL003") is True
            assert config.get_rule_options("PL003") == {
                "only_for_paths": ["src/api/**", "src/auth/**"],
                "skip_utilities": True
            }
    
    @pytest.mark.e2e
    def test_config_error_handling_e2e(self):
        """Test configuration error handling in end-to-end scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            config_file = project / "pyproject.toml"
            
            # Test various malformed configs
            test_cases = [
                # Malformed TOML
                ("invalid toml [[[", ProboscisConfig()),
                # Wrong types
                ("""
[tool.proboscis]
test_directories = "should be a list"
""", ProboscisConfig()),
                # Invalid enum value
                ("""
[tool.proboscis]
output_format = "yaml"
""", ProboscisConfig()),
                # Partially valid config
                ("""
[tool.proboscis]
test_directories = ["tests"]
output_format = "invalid"
fail_on_error = true
""", ProboscisConfig())
            ]
            
            for content, expected_default in test_cases:
                config_file.write_text(content)
                config = ConfigLoader.load_from_file(config_file)
                # Should fall back to defaults on any error
                assert config.test_directories == expected_default.test_directories
                assert config.output_format == expected_default.output_format