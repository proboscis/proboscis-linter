use pyo3::prelude::*;
use rayon::prelude::*;
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::file_discovery::find_python_files;
use crate::models::LintViolation;
use crate::noqa::parse_noqa_rules;

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
fn check_file(file_path: &Path) -> Vec<LintViolation> {
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

    // Check each test function for the appropriate marker
    test_functions
        .into_iter()
        .filter_map(|func| {
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
    LintViolation {
        rule_name: "PL004:require-test-markers".to_string(),
        file_path: file_path.to_str().unwrap_or("").to_string(),
        line_number: func.line_number,
        function_name: func.name.clone(),
        message: format!(
            "[PL004] Test function '{}' is missing required pytest marker.\nExpected: @pytest.mark.{}\nLocation: {}",
            func.name,
            expected_marker,
            file_path.display()
        ),
        severity: "error".to_string(),
    }
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
            // Check the file for violations
            check_file(file_path)
        })
        .collect();

    Ok(violations)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_missing_unit_marker() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test").join("unit").join("test_example.py");
        fs::create_dir_all(test_file.parent().unwrap()).unwrap();
        
        fs::write(&test_file, r#"
def test_something():
    assert True

@pytest.mark.unit
def test_with_marker():
    assert True
"#).unwrap();

        let violations = check_file(&test_file);
        
        assert_eq!(violations.len(), 1);
        assert_eq!(violations[0].function_name, "test_something");
        assert!(violations[0].message.contains("@pytest.mark.unit"));
    }

    #[test]
    fn test_missing_integration_marker() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test").join("integration").join("test_example.py");
        fs::create_dir_all(test_file.parent().unwrap()).unwrap();
        
        fs::write(&test_file, r#"
@pytest.mark.unit
def test_wrong_marker():
    assert True

@pytest.mark.integration
def test_correct_marker():
    assert True
"#).unwrap();

        let violations = check_file(&test_file);
        
        assert_eq!(violations.len(), 1);
        assert_eq!(violations[0].function_name, "test_wrong_marker");
        assert!(violations[0].message.contains("@pytest.mark.integration"));
    }

    #[test]
    fn test_missing_e2e_marker() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test").join("e2e").join("test_example.py");
        fs::create_dir_all(test_file.parent().unwrap()).unwrap();
        
        fs::write(&test_file, r#"
def test_no_marker():
    pass

@mark.e2e  # Short form should also work
def test_short_marker():
    pass

@pytest.mark.e2e
def test_full_marker():
    pass
"#).unwrap();

        let violations = check_file(&test_file);
        
        assert_eq!(violations.len(), 1);
        assert_eq!(violations[0].function_name, "test_no_marker");
    }

    #[test]
    fn test_noqa_suppression() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test").join("unit").join("test_example.py");
        fs::create_dir_all(test_file.parent().unwrap()).unwrap();
        
        fs::write(&test_file, r#"
# noqa: PL004
def test_no_marker_but_suppressed():
    assert True
"#).unwrap();

        let violations = check_file(&test_file);
        assert_eq!(violations.len(), 0);
    }
}