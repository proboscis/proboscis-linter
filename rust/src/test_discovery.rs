use std::fs;
use std::path::Path;
use walkdir::WalkDir;

/// Find test for a function by searching test directories
pub fn find_test_for_function(
    function_name: &str,
    source_path: &Path,
    class_name: Option<&str>,
    _is_method: bool,
    test_directories: &[String],
) -> bool {
    // Find project root (go up until we find a test directory)
    let mut project_root = source_path.parent();
    while let Some(root) = project_root {
        if test_directories.iter().any(|dir| root.join(dir).exists()) {
            break;
        }
        project_root = root.parent();
    }
    
    let project_root = match project_root {
        Some(root) => root,
        None => return false,
    };
    
    // Generate test name patterns
    let mut test_patterns = vec![
        format!("test_{}", function_name),
        format!("test_e2e_{}", function_name),
    ];
    
    if let Some(class) = class_name {
        test_patterns.push(format!("test_{}_{}", class.to_lowercase(), function_name));
        test_patterns.push(format!("test_{}_{}", class, function_name));
    }
    
    // Search for tests in test directories
    for test_dir_name in test_directories {
        let test_dir = project_root.join(test_dir_name);
        if !test_dir.exists() {
            continue;
        }
        
        // Walk through test directory
        for entry in WalkDir::new(&test_dir).into_iter().filter_map(Result::ok) {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) != Some("py") {
                continue;
            }
            
            // Check if this is a test file for our module
            let module_name = source_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            
            let file_name = path.file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            
            if !file_name.contains(module_name) && !file_name.starts_with("test_") {
                continue;
            }
            
            // Read file and search for test functions
            if let Ok(content) = fs::read_to_string(path) {
                for pattern in &test_patterns {
                    if content.contains(&format!("def {}", pattern)) {
                        return true;
                    }
                }
            }
        }
    }
    
    false
}