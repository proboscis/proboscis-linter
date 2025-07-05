mod file_discovery;
mod git;
mod models;
mod noqa;
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
use crate::rules::{get_all_rules, pl004_require_test_markers::check_test_markers};
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
            .filter_map(|file| self.lint_file_internal_with_cache(file, &rules, &test_cache, project_path).ok())
            .flatten()
            .collect();
        
        Ok(violations)
    }

    fn lint_file(&self, file_path: &str) -> PyResult<Vec<LintViolation>> {
        let path = Path::new(file_path);
        let rules = get_all_rules();
        self.lint_file_internal(path, &rules)
    }
    
    fn lint_changed_files(&self, project_root: &str) -> PyResult<Vec<LintViolation>> {
        let project_path = Path::new(project_root);
        
        // Check if we're in a git repository
        if !git::is_git_repository(project_path) {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "Not in a git repository"
            ));
        }
        
        // Get changed files
        let changed_files = git::get_changed_files(project_path);
        
        if changed_files.is_empty() {
            return Ok(Vec::new());
        }
        
        // Build test cache once for the entire project
        let test_cache = TestCache::build_from_directories(project_path, &self.test_directories);
        
        // Get all rules
        let rules = get_all_rules();
        
        // Process changed files in parallel with shared test cache
        let violations: Vec<LintViolation> = changed_files
            .par_iter()
            .filter_map(|file| self.lint_file_internal_with_cache(file, &rules, &test_cache, project_path).ok())
            .flatten()
            .collect();
        
        Ok(violations)
    }
    
    fn check_test_markers(&self, project_root: &str) -> PyResult<Vec<LintViolation>> {
        let project_path = Path::new(project_root);
        let violations = check_test_markers(
            project_path.to_path_buf(),
            self.test_directories.clone(),
            self.exclude_patterns.clone(),
        )?;
        Ok(violations)
    }
}

impl RustLinter {
    /// Extract module path from file path (e.g., src/pkg/mod1/submod.py -> pkg.mod1.submod)
    fn get_module_path(file_path: &Path, project_root: &Path) -> String {
        // Get relative path from project root
        let relative_path = file_path.strip_prefix(project_root).unwrap_or(file_path);
        
        // Remove src/ prefix if present
        let module_path = if let Ok(stripped) = relative_path.strip_prefix("src") {
            stripped
        } else {
            relative_path
        };
        
        // Convert path to module notation
        let mut components = Vec::new();
        for component in module_path.components() {
            if let Some(s) = component.as_os_str().to_str() {
                // Remove .py extension from the last component
                let part = if s.ends_with(".py") {
                    &s[..s.len() - 3]
                } else {
                    s
                };
                // Skip __init__ files
                if part != "__init__" && !part.is_empty() {
                    components.push(part);
                }
            }
        }
        
        components.join(".")
    }
    
    fn lint_file_internal(
        &self,
        path: &Path,
        rules: &[Box<dyn rules::LintRule + Send + Sync>],
    ) -> PyResult<Vec<LintViolation>> {
        // For single file linting, find project root by looking for pyproject.toml or setup.py
        let mut project_root = path.parent().unwrap_or(Path::new("."));
        let mut current = project_root;
        while current != current.parent().unwrap_or(current) {
            if current.join("pyproject.toml").exists() || current.join("setup.py").exists() {
                project_root = current;
                break;
            }
            current = current.parent().unwrap_or(current);
        }
        
        let test_cache = TestCache::build_from_directories(project_root, &self.test_directories);
        self.lint_file_internal_with_cache(path, rules, &test_cache, project_root)
    }
    
    fn lint_file_internal_with_cache(
        &self,
        path: &Path,
        rules: &[Box<dyn rules::LintRule + Send + Sync>],
        test_cache: &std::sync::Arc<TestCache>,
        project_root: &Path,
    ) -> PyResult<Vec<LintViolation>> {
        let content = fs::read_to_string(path)?;
        let lines: Vec<&str> = content.lines().collect();
        
        // Get module path for this file
        let module_path = Self::get_module_path(path, project_root);
        
        let mut violations = Vec::new();
        let mut current_class = None;
        let mut in_protocol = false;
        
        for (line_num, line) in lines.iter().enumerate() {
            // Check for class definitions
            if let Some(captures) = self.class_regex.captures(line) {
                let class_name = captures.get(2).unwrap().as_str();
                current_class = Some(class_name.to_string());
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
                    module_path: &module_path,
                    project_root,
                };
                
                // Check against all rules
                for rule in rules {
                    // If we have a current class and the function is indented, it's a method
                    let is_method = current_class.is_some() && !indent.is_empty();
                    let is_protocol_method = in_protocol && is_method;
                    
                    if let Some(violation) = rule.check_function(
                        function_name,
                        path,
                        line_num + 1,
                        line,
                        if is_method { current_class.as_deref() } else { None },
                        is_protocol_method,
                        &context,
                    ) {
                        violations.push(violation);
                    }
                }
            }
            
            // Reset class context on dedent (non-blank line with no indentation)
            // But skip if it's a class or function definition
            if current_class.is_some() && !line.trim().is_empty() && !line.starts_with(' ') && !line.starts_with('\t') {
                // Don't reset if this line is defining a new class or function at module level
                if !self.class_regex.is_match(line) && !self.function_regex.is_match(line) {
                    current_class = None;
                    in_protocol = false;
                }
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