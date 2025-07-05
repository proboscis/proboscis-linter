use super::LintRule;
use crate::models::LintViolation;
use crate::test_discovery::find_test_for_function;
use regex::Regex;
use std::path::Path;

pub struct PL001RequireTest {
    noqa_regex: Regex,
}

impl PL001RequireTest {
    pub fn new() -> Self {
        Self {
            noqa_regex: Regex::new(r"#\s*noqa:\s*PL001").unwrap(),
        }
    }
}

impl LintRule for PL001RequireTest {
    fn rule_id(&self) -> &'static str {
        "PL001"
    }
    
    fn rule_name(&self) -> &'static str {
        "require-test"
    }
    
    fn check_function(
        &self,
        function_name: &str,
        file_path: &Path,
        line_number: usize,
        line_content: &str,
        class_name: Option<&str>,
        is_protocol: bool,
        context: &super::RuleContext,
    ) -> Option<LintViolation> {
        // Skip if has noqa comment
        if self.noqa_regex.is_match(line_content) {
            return None;
        }
        
        // Skip protocol methods
        if is_protocol && class_name.is_some() {
            return None;
        }
        
        // Skip __init__ and private methods
        if function_name == "__init__" || function_name.starts_with('_') {
            return None;
        }
        
        // Check if it's a method (has class context)
        let is_method = class_name.is_some();
        
        // Look for corresponding test
        let test_found = find_test_for_function(
            function_name,
            file_path,
            class_name,
            is_method,
            context.test_directories,
        );
        
        if !test_found {
            Some(LintViolation {
                rule_name: format!("{}:{}", self.rule_id(), self.rule_name()),
                file_path: file_path.to_string_lossy().to_string(),
                line_number,
                function_name: function_name.to_string(),
                message: format!(
                    "[{}] Function '{}' at {}:{} has no test found",
                    self.rule_id(),
                    function_name,
                    file_path.display(),
                    line_number
                ),
                severity: "error".to_string(),
            })
        } else {
            None
        }
    }
}