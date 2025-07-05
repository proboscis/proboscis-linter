mod file_discovery;
mod models;
mod rules;
mod test_cache;
mod test_discovery;

use pyo3::prelude::*;
use rayon::prelude::*;
use regex::Regex;
use std::fs;
use std::path::Path;

use crate::file_discovery::find_python_files;
use crate::models::LintViolation;
use crate::rules::get_all_rules;
use crate::test_cache::TestCache;

#[pyclass]
#[derive(Clone)]
pub struct RustLinter {
    test_directories: Vec<String>,
    test_patterns: Vec<String>,
    exclude_patterns: Vec<String>,
    function_regex: Regex,
    class_regex: Regex,
}

#[pymethods]
impl RustLinter {
    #[new]
    #[pyo3(signature = (test_directories=None, test_patterns=None, exclude_patterns=None))]
    fn new(
        test_directories: Option<Vec<String>>,
        test_patterns: Option<Vec<String>>,
        exclude_patterns: Option<Vec<String>>,
    ) -> PyResult<Self> {
        Ok(Self {
            test_directories: test_directories.unwrap_or_else(|| vec!["test".to_string(), "tests".to_string()]),
            test_patterns: test_patterns.unwrap_or_else(|| vec!["test_*.py".to_string(), "*_test.py".to_string()]),
            exclude_patterns: exclude_patterns.unwrap_or_default(),
            function_regex: Regex::new(r"^(\s*)def\s+(\w+)\s*\(").unwrap(),
            class_regex: Regex::new(r"^(\s*)class\s+(\w+)").unwrap(),
        })
    }

    fn lint_project(&self, project_root: &str) -> PyResult<Vec<LintViolation>> {
        let project_path = Path::new(project_root);
        
        // Build test cache once for the entire project
        let test_cache = TestCache::build_from_directories(project_path, &self.test_directories);
        
        // Find all Python files
        let python_files = find_python_files(project_path, &self.exclude_patterns);
        
        // Get all rules
        let rules = get_all_rules();
        
        // Process files in parallel with shared test cache
        let violations: Vec<LintViolation> = python_files
            .par_iter()
            .filter_map(|file| self.lint_file_internal_with_cache(file, &rules, &test_cache).ok())
            .flatten()
            .collect();
        
        Ok(violations)
    }

    fn lint_file(&self, file_path: &str) -> PyResult<Vec<LintViolation>> {
        let path = Path::new(file_path);
        let rules = get_all_rules();
        self.lint_file_internal(path, &rules)
    }
}

impl RustLinter {
    fn lint_file_internal(
        &self,
        path: &Path,
        rules: &[Box<dyn rules::LintRule + Send + Sync>],
    ) -> PyResult<Vec<LintViolation>> {
        // For single file linting, build a small cache
        let project_root = path.parent().unwrap_or(Path::new("."));
        let test_cache = TestCache::build_from_directories(project_root, &self.test_directories);
        self.lint_file_internal_with_cache(path, rules, &test_cache)
    }
    
    fn lint_file_internal_with_cache(
        &self,
        path: &Path,
        rules: &[Box<dyn rules::LintRule + Send + Sync>],
        test_cache: &std::sync::Arc<TestCache>,
    ) -> PyResult<Vec<LintViolation>> {
        let content = fs::read_to_string(path)?;
        let lines: Vec<&str> = content.lines().collect();
        
        let mut violations = Vec::new();
        let mut current_class = None;
        let mut in_protocol = false;
        
        for (line_num, line) in lines.iter().enumerate() {
            // Check for class definitions
            if let Some(captures) = self.class_regex.captures(line) {
                current_class = Some(captures.get(2).unwrap().as_str().to_string());
                in_protocol = line.contains("Protocol");
                continue;
            }
            
            // Check for function definitions
            if let Some(captures) = self.function_regex.captures(line) {
                let indent = captures.get(1).unwrap().as_str();
                let function_name = captures.get(2).unwrap().as_str();
                
                // Create rule context
                let context = rules::RuleContext {
                    test_directories: &self.test_directories,
                    test_cache,
                };
                
                // Check against all rules
                for rule in rules {
                    if let Some(violation) = rule.check_function(
                        function_name,
                        path,
                        line_num + 1,
                        line,
                        current_class.as_deref(),
                        in_protocol && !indent.is_empty(),
                        &context,
                    ) {
                        violations.push(violation);
                    }
                }
            }
            
            // Reset class context on dedent
            if current_class.is_some() && line.chars().all(|c| c.is_whitespace()) {
                current_class = None;
                in_protocol = false;
            }
        }
        
        Ok(violations)
    }
}

/// Python module initialization
#[pymodule]
fn proboscis_linter_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustLinter>()?;
    m.add_class::<LintViolation>()?;
    Ok(())
}