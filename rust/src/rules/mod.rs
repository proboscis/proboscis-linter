pub mod pl001_require_test;
pub mod pl002_require_integration_test;
pub mod pl003_require_e2e_test;
pub mod pl004_require_test_markers;

use crate::models::LintViolation;
use std::path::Path;

use crate::test_cache::TestCache;
use std::sync::Arc;

/// Context for rule checking
pub struct RuleContext<'a> {
    pub test_directories: &'a [String],
    pub test_cache: &'a Arc<TestCache>,
    pub module_path: &'a str,
    pub project_root: &'a Path,
}

/// Trait that all linting rules must implement
pub trait LintRule {
    /// Get the rule ID (e.g., "PL001")
    fn rule_id(&self) -> &'static str;

    /// Get the rule name (e.g., "require-test")
    fn rule_name(&self) -> &'static str;

    /// Check if a function violates this rule
    fn check_function(
        &self,
        function_name: &str,
        file_path: &Path,
        line_number: usize,
        line_content: &str,
        class_name: Option<&str>,
        is_protocol: bool,
        context: &RuleContext,
    ) -> Option<LintViolation>;
}

/// Get all available rules
pub fn get_all_rules() -> Vec<Box<dyn LintRule + Send + Sync>> {
    vec![
        Box::new(pl001_require_test::PL001RequireUnitTest::new()),
        Box::new(pl002_require_integration_test::PL002RequireIntegrationTest::new()),
        Box::new(pl003_require_e2e_test::PL003RequireE2ETest::new()),
    ]
}
