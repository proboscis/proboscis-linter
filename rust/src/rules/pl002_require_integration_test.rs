use super::LintRule;
use crate::models::LintViolation;
use crate::noqa::parse_noqa_rules;
use std::path::Path;

pub struct PL002RequireIntegrationTest {}

impl PL002RequireIntegrationTest {
    pub fn new() -> Self {
        Self {}
    }
}

impl LintRule for PL002RequireIntegrationTest {
    fn rule_id(&self) -> &'static str {
        "PL002"
    }

    fn rule_name(&self) -> &'static str {
        "require-integration-test"
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
        let suppressed_rules = parse_noqa_rules(line_content);
        if suppressed_rules.contains(self.rule_id()) {
            return None;
        }

        // Skip protocol methods
        if is_protocol && class_name.is_some() {
            return None;
        }

        // Skip __init__ (special case)
        if function_name == "__init__" {
            return None;
        }

        // Look for corresponding integration test using cache
        let test_found = context.test_cache.has_test_for_function_of_type(
            function_name,
            file_path,
            class_name,
            &crate::test_cache::TestType::Integration,
            context.module_path,
            context.project_root,
        );

        if !test_found {
            // Get the single canonical test pattern
            let test_name = context.test_cache.get_canonical_test_pattern(
                function_name,
                class_name,
                &crate::test_cache::TestType::Integration,
            );

            // Get source file name
            let source_file_name = file_path
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("module.py");

            // Get absolute path where test should be located
            let expected_test_file = context.test_cache.get_expected_test_file_path(
                context.module_path,
                source_file_name,
                &crate::test_cache::TestType::Integration,
                context.project_root,
            );

            let message = if let Some(class) = class_name {
                format!(
                    "[{}] Method '{}' of class '{}' has no integration test found.\nExpected test function: {}\nIn test file: {}",
                    self.rule_id(),
                    function_name,
                    class,
                    test_name,
                    expected_test_file.display()
                )
            } else {
                format!(
                    "[{}] Function '{}' has no integration test found.\nExpected test function: {}\nIn test file: {}",
                    self.rule_id(),
                    function_name,
                    test_name,
                    expected_test_file.display()
                )
            };

            Some(LintViolation {
                rule_name: format!("{}:{}", self.rule_id(), self.rule_name()),
                file_path: file_path.to_string_lossy().to_string(),
                line_number,
                function_name: function_name.to_string(),
                message,
                severity: "error".to_string(),
                fix_type: None,
                fix_content: None,
                fix_line: None,
            })
        } else {
            None
        }
    }
}
