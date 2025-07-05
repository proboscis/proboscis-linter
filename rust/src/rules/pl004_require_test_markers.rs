use pyo3::prelude::*;
use rayon::prelude::*;
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::file_discovery::find_python_files;
use crate::models::LintViolation;
use crate::noqa::parse_noqa_rules;
use crate::public_api;

/// PL004: Require pytest markers on test functions
/// 
/// This rule ensures that test functions have the appropriate pytest marker
/// based on their location in the test hierarchy:
/// - Tests in test/unit/ should have @pytest.mark.unit
/// - Tests in test/integration/ should have @pytest.mark.integration  
/// - Tests in test/e2e/ should have @pytest.mark.e2e

struct TestFunction {
    name: String,
    line_number: usize,
    decorators: Vec<String>,
}

/// Extract test functions from a Python file
fn extract_test_functions(file_path: &Path) -> Result<Vec<TestFunction>, std::io::Error> {
    let content = fs::read_to_string(file_path)?;
    let mut functions = Vec::new();
    
    let func_regex = Regex::new(r"^(\s*)def\s+(test_\w+)\s*\(").unwrap();
    let decorator_regex = Regex::new(r"^(\s*)@(.+)$").unwrap();
    
    let lines: Vec<&str> = content.lines().collect();
    let mut i = 0;
    
    while i < lines.len() {
        if let Some(func_captures) = func_regex.captures(lines[i]) {
            let func_name = func_captures.get(2).unwrap().as_str().to_string();
            let func_line = i + 1;
            
            // Look back for decorators
            let mut decorators = Vec::new();
            let mut j = i as i32 - 1;
            
            // Go backwards to find decorators
            while j >= 0 {
                let line_idx = j as usize;
                if !lines[line_idx].trim().starts_with('@') {
                    break;
                }
                if let Some(dec_captures) = decorator_regex.captures(lines[line_idx]) {
                    let decorator_raw = dec_captures.get(2).unwrap().as_str();
                    // Remove inline comments
                    let decorator = if let Some(comment_pos) = decorator_raw.find('#') {
                        decorator_raw[..comment_pos].trim().to_string()
                    } else {
                        decorator_raw.trim().to_string()
                    };
                    decorators.push(decorator);
                }
                j -= 1;
            }
            
            decorators.reverse(); // Put them in the correct order
            
            functions.push(TestFunction {
                name: func_name,
                line_number: func_line,
                decorators,
            });
        }
        i += 1;
    }
    
    Ok(functions)
}

/// Extract all noqa rules from a file
fn extract_file_noqa_rules(file_path: &Path) -> Result<HashSet<String>, std::io::Error> {
    let content = fs::read_to_string(file_path)?;
    let mut all_rules = HashSet::new();
    
    // Check for file-level noqa at the beginning
    let lines: Vec<&str> = content.lines().collect();
    let mut file_level_noqa = false;
    
    // Check first few non-empty lines for file-level noqa
    for (i, line) in lines.iter().enumerate().take(5) {
        if line.trim().is_empty() {
            continue;
        }
        if !line.trim().starts_with('#') && !line.trim().starts_with("\"\"\"") {
            break;  // Stop at first code line
        }
        let rules = parse_noqa_rules(line);
        if rules.contains(&"PL004".to_string()) && i < 3 {
            // Consider it file-level if in first 3 lines
            file_level_noqa = true;
            all_rules.insert("PL004".to_string());
        }
    }
    
    // Extract line-specific noqa rules
    if !file_level_noqa {
        for (line_num, line) in lines.iter().enumerate() {
            let rules = parse_noqa_rules(line);
            for rule in rules {
                // Only add line-specific version
                all_rules.insert(format!("{}:{}", line_num + 1, rule));
            }
        }
    }
    
    Ok(all_rules)
}

/// Check a single test file for missing pytest markers
fn check_file(file_path: &Path, source_module_path: Option<&Path>) -> Vec<LintViolation> {
    // Extract noqa rules for this file
    let noqa_rules = extract_file_noqa_rules(file_path).unwrap_or_default();
    
    // Skip if PL004 is suppressed for this file
    if noqa_rules.contains("PL004") {
        return vec![];
    }

    // Determine the expected marker based on the file path
    let expected_marker = match get_test_type_from_path(file_path) {
        Some(test_type) => test_type,
        None => return vec![], // Not in a recognized test directory
    };

    // Extract test functions from the file
    let test_functions = match extract_test_functions(file_path) {
        Ok(funcs) => funcs,
        Err(_) => return vec![],
    };
    
    // Extract public API from source module if available
    let public_api = if let Some(source_path) = source_module_path {
        public_api::extract_module_all(source_path).unwrap_or(public_api::PublicApi::default())
    } else {
        public_api::PublicApi::default()
    };

    // Check each test function for the appropriate marker
    test_functions
        .into_iter()
        .filter_map(|func| {
            // Try to infer what function this test is testing
            let tested_func = infer_tested_function(&func.name);
            
            // Skip if testing a private function
            if let Some(tested) = &tested_func {
                if !should_check_test_for_function(tested, &public_api) {
                    return None;
                }
            }
            
            // Skip if the line has noqa
            let line_noqa = noqa_rules.contains(&format!("{}:PL004", func.line_number));
            if line_noqa || has_pytest_marker(&func, &expected_marker) {
                None
            } else {
                Some(create_violation(file_path, &func, &expected_marker))
            }
        })
        .collect()
}

/// Determine test type from file path
fn get_test_type_from_path(file_path: &Path) -> Option<String> {
    let path_str = file_path.to_string_lossy();
    
    if path_str.contains("/unit/") || path_str.contains("\\unit\\") {
        Some("unit".to_string())
    } else if path_str.contains("/integration/") || path_str.contains("\\integration\\") {
        Some("integration".to_string())
    } else if path_str.contains("/e2e/") || path_str.contains("\\e2e\\") {
        Some("e2e".to_string())
    } else {
        None
    }
}

/// Check if a function has the required pytest marker
fn has_pytest_marker(func: &TestFunction, expected_marker: &str) -> bool {
    // Check if any decorator matches pytest.mark.{expected_marker}
    func.decorators.iter().any(|decorator| {
        // Handle various forms: pytest.mark.unit, mark.unit, unit
        let dec = decorator.trim();
        dec == &format!("pytest.mark.{}", expected_marker) ||
        dec == &format!("mark.{}", expected_marker) ||
        dec == expected_marker ||
        // Handle parentheses: pytest.mark.unit(), mark.unit()
        dec == &format!("pytest.mark.{}()", expected_marker) ||
        dec == &format!("mark.{}()", expected_marker)
    })
}

/// Create a violation for a missing pytest marker
fn create_violation(file_path: &Path, func: &TestFunction, expected_marker: &str) -> LintViolation {
    // The fix is to add the decorator on the line before the function
    let fix_line = if func.line_number > 1 { func.line_number - 1 } else { 1 };
    
    LintViolation {
        rule_name: "PL004:require-test-markers".to_string(),
        file_path: file_path.to_str().unwrap_or("").to_string(),
        line_number: func.line_number,
        function_name: func.name.clone(),
        message: format!(
            "[PL004] Test function '{}' is missing required pytest marker.\nExpected: @pytest.mark.{}\nLocation: {}\n\nTip: Use --fix flag to automatically add missing markers",
            func.name,
            expected_marker,
            file_path.display()
        ),
        severity: "error".to_string(),
        fix_type: Some("add_decorator".to_string()),
        fix_content: Some(format!("@pytest.mark.{}", expected_marker)),
        fix_line: Some(fix_line),
    }
}

/// Infer the function being tested from the test function name
fn infer_tested_function(test_name: &str) -> Option<String> {
    // Common patterns:
    // test_function_name -> function_name
    // test_method_name -> method_name
    // test_ClassName_method -> ClassName.method
    
    if test_name.starts_with("test_") {
        let without_prefix = &test_name[5..];
        
        // Check for class method pattern (test_ClassName_method)
        if let Some(underscore_pos) = without_prefix.find('_') {
            let potential_class = &without_prefix[..underscore_pos];
            // Check if first letter is uppercase (likely a class name)
            if potential_class.chars().next().map_or(false, |c| c.is_uppercase()) {
                return Some(without_prefix.to_string());
            }
        }
        
        // Regular function pattern
        Some(without_prefix.to_string())
    } else {
        None
    }
}

/// Check if we should check a test based on what it's testing
fn should_check_test_for_function(tested_func: &str, public_api: &public_api::PublicApi) -> bool {
    // For tests, we always use the default (non-strict) mode
    // This means we only check tests for public functions
    
    // Check for class.method pattern
    if let Some(dot_pos) = tested_func.find('.') {
        let class_name = &tested_func[..dot_pos];
        let method_name = &tested_func[dot_pos + 1..];
        
        // Skip if method starts with underscore
        if method_name.starts_with('_') {
            return false;
        }
        
        // Check if class is public
        public_api.is_public(class_name)
    } else {
        // Regular function - check if it's public
        public_api.is_public(tested_func)
    }
}

/// Find the source module that corresponds to a test file
fn find_source_module_for_test(test_path: &Path, project_root: &Path) -> Option<PathBuf> {
    // Get the test file name without test_ prefix
    let test_file_name = test_path.file_name()?.to_str()?;
    
    // Remove test_ prefix or _test suffix to get source file name
    let source_file_name = if test_file_name.starts_with("test_") && test_file_name.ends_with(".py") {
        // test_module.py -> module.py
        format!("{}.py", &test_file_name[5..test_file_name.len()-3])
    } else if test_file_name.ends_with("_test.py") {
        // module_test.py -> module.py
        format!("{}.py", &test_file_name[..test_file_name.len()-8])
    } else {
        return None;
    };
    
    // Try to find the source file in the project
    // Look in common source directories
    for src_dir in &["src", "lib", "."] {
        let src_path = project_root.join(src_dir);
        if src_path.exists() {
            // Walk the source directory to find the module
            if let Ok(entries) = fs::read_dir(&src_path) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_file() && path.file_name().map_or(false, |n| n == source_file_name.as_str()) {
                        return Some(path);
                    }
                }
            }
        }
    }
    
    // Also check the parent directory of the test file
    if let Some(parent) = test_path.parent() {
        let potential_source = parent.join(&source_file_name);
        if potential_source.exists() {
            return Some(potential_source);
        }
    }
    
    None
}

/// Check all test files in a project for missing pytest markers
#[pyfunction]
pub fn check_test_markers(
    project_root: PathBuf,
    test_directories: Vec<String>,
    exclude_patterns: Vec<String>,
) -> PyResult<Vec<LintViolation>> {
    
    // Find all test files in the test directories
    let test_files: Vec<PathBuf> = test_directories
        .par_iter()
        .flat_map(|test_dir| {
            let test_path = project_root.join(test_dir);
            if test_path.exists() {
                find_python_files(&test_path, &exclude_patterns)
                    .into_iter()
                    .filter(|path| {
                        // Only check files that start with test_ or end with _test.py
                        if let Some(file_name) = path.file_name() {
                            let name = file_name.to_string_lossy();
                            name.starts_with("test_") || name.ends_with("_test.py")
                        } else {
                            false
                        }
                    })
                    .collect::<Vec<_>>()
            } else {
                vec![]
            }
        })
        .collect();

    // Check each test file for violations
    let violations: Vec<LintViolation> = test_files
        .par_iter()
        .flat_map(|file_path| {
            // Try to find corresponding source module
            let source_module_path = find_source_module_for_test(file_path, &project_root);
            
            // Check the file for violations
            check_file(file_path, source_module_path.as_deref())
        })
        .collect();

    Ok(violations)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_infer_tested_function() {
        // Test regular function pattern
        assert_eq!(
            infer_tested_function("test_my_function"),
            Some("my_function".to_string())
        );
        
        // Test class method pattern
        assert_eq!(
            infer_tested_function("test_MyClass_method"),
            Some("MyClass_method".to_string())
        );
        
        // Test underscore in function name
        assert_eq!(
            infer_tested_function("test_function_with_underscores"),
            Some("function_with_underscores".to_string())
        );
        
        // Test non-test function
        assert_eq!(
            infer_tested_function("not_a_test"),
            None
        );
    }

    #[test]
    fn test_should_check_test_for_function() {
        let mut names = HashSet::new();
        names.insert("public_func".to_string());
        names.insert("PublicClass".to_string());
        
        let public_api = public_api::PublicApi {
            all_names: Some(names),
        };
        
        // Test public function
        assert!(should_check_test_for_function("public_func", &public_api));
        
        // Test private function
        assert!(!should_check_test_for_function("private_func", &public_api));
        
        // Test public class method
        assert!(should_check_test_for_function("PublicClass.method", &public_api));
        
        // Test private class method (underscore)
        assert!(!should_check_test_for_function("PublicClass._private_method", &public_api));
        
        // Test private class
        assert!(!should_check_test_for_function("PrivateClass.method", &public_api));
    }
    
    #[test]
    fn test_get_test_type_from_path() {
        use std::path::PathBuf;
        
        // Unit test path
        let unit_path = PathBuf::from("/project/test/unit/test_example.py");
        assert_eq!(get_test_type_from_path(&unit_path), Some("unit".to_string()));
        
        // Integration test path
        let integration_path = PathBuf::from("/project/test/integration/test_example.py");
        assert_eq!(get_test_type_from_path(&integration_path), Some("integration".to_string()));
        
        // E2E test path
        let e2e_path = PathBuf::from("/project/test/e2e/test_example.py");
        assert_eq!(get_test_type_from_path(&e2e_path), Some("e2e".to_string()));
        
        // Non-test path
        let other_path = PathBuf::from("/project/test/other/test_example.py");
        assert_eq!(get_test_type_from_path(&other_path), None);
    }
}