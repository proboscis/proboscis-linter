# Adding New Rules to Proboscis Linter

This guide explains how to add new linting rules to the Rust implementation of Proboscis Linter.

## Rule Naming Convention

All rules must follow the `PL###` naming convention:
- `PL001` - require-test (functions must have tests)
- `PL002` - next rule
- `PL003` - and so on...

## Steps to Add a New Rule

### 1. Create the Rule Module

Create a new file in `rust/src/rules/` with the pattern `pl###_rule_name.rs`:

```rust
// rust/src/rules/pl002_docstring.rs
use super::{LintRule, RuleContext};
use crate::models::LintViolation;
use regex::Regex;
use std::path::Path;

pub struct PL002Docstring {
    noqa_regex: Regex,
}

impl PL002Docstring {
    pub fn new() -> Self {
        Self {
            noqa_regex: Regex::new(r"#\s*noqa:\s*PL002").unwrap(),
        }
    }
}

impl LintRule for PL002Docstring {
    fn rule_id(&self) -> &'static str {
        "PL002"
    }
    
    fn rule_name(&self) -> &'static str {
        "require-docstring"
    }
    
    fn check_function(
        &self,
        function_name: &str,
        file_path: &Path,
        line_number: usize,
        line_content: &str,
        class_name: Option<&str>,
        is_protocol: bool,
        context: &RuleContext,
    ) -> Option<LintViolation> {
        // Skip if has noqa comment
        if self.noqa_regex.is_match(line_content) {
            return None;
        }
        
        // Your rule logic here
        // Return Some(LintViolation) if rule is violated
        // Return None if rule passes
        
        None
    }
}
```

### 2. Register the Rule

Add your rule to the module exports in `rust/src/rules/mod.rs`:

```rust
pub mod pl001_require_test;
pub mod pl002_docstring;  // Add this line

// In get_all_rules() function:
pub fn get_all_rules() -> Vec<Box<dyn LintRule + Send + Sync>> {
    vec![
        Box::new(pl001_require_test::PL001RequireTest::new()),
        Box::new(pl002_docstring::PL002Docstring::new()),  // Add this line
    ]
}
```

### 3. Configure the Rule

Add the rule to your `pyproject.toml` configuration:

```toml
[tool.proboscis.rules]
PL001 = true  # require-test rule
PL002 = true  # require-docstring rule
```

Or with options:

```toml
[tool.proboscis.rules.PL002]
enabled = true
min_length = 10
```

### 4. Rebuild and Test

Rebuild the Rust extension:
```bash
uv run maturin develop
```

Test your new rule:
```bash
PYTHONPATH=. uv run python -m proboscis_linter test_file.py
```

## Rule Context

The `RuleContext` provides access to configuration and shared resources:

- `context.test_directories` - List of test directory names to search

## Best Practices

1. **Naming**: Use descriptive rule names that clearly indicate what the rule checks
2. **Messages**: Provide clear, actionable error messages
3. **Performance**: Rules are run in parallel, ensure thread safety
4. **Skipping**: Always check for `noqa` comments specific to your rule
5. **Documentation**: Document what your rule checks and why

## Example: Adding a Docstring Rule

Here's a complete example of adding a rule that requires functions to have docstrings:

```rust
// rust/src/rules/pl002_docstring.rs
use super::{LintRule, RuleContext};
use crate::models::LintViolation;
use regex::Regex;
use std::path::Path;

pub struct PL002Docstring {
    noqa_regex: Regex,
}

impl PL002Docstring {
    pub fn new() -> Self {
        Self {
            noqa_regex: Regex::new(r"#\s*noqa:\s*PL002").unwrap(),
        }
    }
}

impl LintRule for PL002Docstring {
    fn rule_id(&self) -> &'static str {
        "PL002"
    }
    
    fn rule_name(&self) -> &'static str {
        "require-docstring"
    }
    
    fn check_function(
        &self,
        function_name: &str,
        file_path: &Path,
        line_number: usize,
        line_content: &str,
        class_name: Option<&str>,
        is_protocol: bool,
        context: &RuleContext,
    ) -> Option<LintViolation> {
        // Skip if has noqa comment
        if self.noqa_regex.is_match(line_content) {
            return None;
        }
        
        // Skip dunder methods
        if function_name.starts_with("__") && function_name.ends_with("__") {
            return None;
        }
        
        // In a real implementation, you would check the following lines
        // for a docstring. This is a simplified example.
        Some(LintViolation {
            rule_name: format!("{}:{}", self.rule_id(), self.rule_name()),
            file_path: file_path.to_string_lossy().to_string(),
            line_number,
            function_name: function_name.to_string(),
            message: format!(
                "[{}] Function '{}' has no docstring",
                self.rule_id(),
                function_name
            ),
            severity: "warning".to_string(),
        })
    }
}
```

## Testing Your Rule

Create tests for your rule in the Python test suite:

```python
# tests/unit/test_pl002_docstring.py
import pytest
from proboscis_linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig

def test_docstring_rule(tmp_path):
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text('''
def function_without_docstring():
    pass

def function_with_docstring():
    """This function has a docstring."""
    pass
''')
    
    config = ProboscisConfig(rules={"PL002": True})
    linter = ProboscisLinter(config)
    violations = linter.lint_file(test_file, [])
    
    assert len(violations) == 1
    assert violations[0].rule_name == "PL002:require-docstring"
    assert violations[0].function_name == "function_without_docstring"
```