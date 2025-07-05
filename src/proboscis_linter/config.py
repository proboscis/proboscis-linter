"""Configuration management for proboscis-linter."""
from pathlib import Path
from typing import Dict, List, Optional, Any
import tomllib
from pydantic import BaseModel, Field, field_validator
from loguru import logger


class RuleConfig(BaseModel):
    """Configuration for individual rules."""
    enabled: bool = True
    options: Dict[str, Any] = Field(default_factory=dict)


class ProboscisConfig(BaseModel):
    """Configuration model for proboscis-linter."""
    
    # Test discovery configuration
    test_directories: List[str] = Field(
        default_factory=lambda: ["test", "tests"],
        description="Directories to search for test files"
    )
    test_patterns: List[str] = Field(
        default_factory=lambda: ["test_*.py", "*_test.py"],
        description="File patterns for test discovery"
    )
    
    # File filtering
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="Glob patterns for files/directories to exclude from linting"
    )
    
    # Rule configuration
    rules: Dict[str, RuleConfig] = Field(
        default_factory=dict,
        description="Rule-specific configuration"
    )
    
    # Output configuration
    output_format: str = Field(
        default="text",
        description="Default output format (text or json)"
    )
    fail_on_error: bool = Field(
        default=False,
        description="Exit with non-zero code if violations are found"
    )
    
    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        if v not in ["text", "json"]:
            raise ValueError(f"Invalid output format: {v}. Must be 'text' or 'json'")
        return v
    
    @field_validator("test_directories", "test_patterns")
    @classmethod
    def validate_non_empty_list(cls, v: List[str]) -> List[str]:
        """Ensure lists are not empty."""
        if not v:
            raise ValueError("List cannot be empty")
        return v
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        if rule_id not in self.rules:
            return True  # Rules are enabled by default
        return self.rules[rule_id].enabled
    
    def get_rule_options(self, rule_id: str) -> Dict[str, Any]:
        """Get options for a specific rule."""
        if rule_id not in self.rules:
            return {}
        return self.rules[rule_id].options


class ConfigLoader:
    """Loads configuration from pyproject.toml."""
    
    @staticmethod
    def load_from_file(config_path: Path) -> ProboscisConfig:
        """Load configuration from a pyproject.toml file."""
        with logger.contextualize(config_file=str(config_path)):
            if not config_path.exists():
                logger.debug("No pyproject.toml found, using defaults")
                return ProboscisConfig()
            
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)
                
                # Extract proboscis configuration
                proboscis_data = data.get("tool", {}).get("proboscis", {})
                
                if not proboscis_data:
                    logger.debug("No [tool.proboscis] section found, using defaults")
                    return ProboscisConfig()
                
                # Convert rule configuration
                rules_data = proboscis_data.get("rules", {})
                rules_config = {}
                
                for rule_id, rule_value in rules_data.items():
                    if isinstance(rule_value, bool):
                        rules_config[rule_id] = RuleConfig(enabled=rule_value)
                    elif isinstance(rule_value, dict):
                        rules_config[rule_id] = RuleConfig(**rule_value)
                    else:
                        logger.warning(f"Invalid rule configuration for {rule_id}: {rule_value}")
                
                proboscis_data["rules"] = rules_config
                
                config = ProboscisConfig(**proboscis_data)
                logger.info("Loaded configuration from pyproject.toml")
                return config
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Using default configuration")
                return ProboscisConfig()
    
    @staticmethod
    def find_config_file(start_path: Path) -> Optional[Path]:
        """Find pyproject.toml by traversing up the directory tree."""
        current = start_path.resolve()
        
        while current != current.parent:
            config_file = current / "pyproject.toml"
            if config_file.exists():
                # Check if it has [tool.proboscis] section
                try:
                    with open(config_file, "rb") as f:
                        data = tomllib.load(f)
                    if "tool" in data and "proboscis" in data["tool"]:
                        logger.debug(f"Found configuration at {config_file}")
                        return config_file
                except Exception:
                    pass
            
            current = current.parent
        
        return None
    
    @staticmethod
    def merge_cli_options(config: ProboscisConfig, **cli_options) -> ProboscisConfig:
        """Merge CLI options with configuration."""
        # Create a copy of the config
        merged_data = config.model_dump()
        
        # Override with CLI options if provided
        if cli_options.get("format") is not None:
            merged_data["output_format"] = cli_options["format"]
        
        if cli_options.get("fail_on_error") is not None:
            merged_data["fail_on_error"] = cli_options["fail_on_error"]
        
        if cli_options.get("exclude"):
            # CLI excludes extend the config excludes
            merged_data["exclude_patterns"].extend(cli_options["exclude"])
        
        return ProboscisConfig(**merged_data)