use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use regex::Regex;
use walkdir::WalkDir;
use rayon::prelude::*;

/// Cache for test file contents and patterns
pub struct TestCache {
    /// Map from test file path to set of function names defined in that file
    test_functions: HashMap<PathBuf, HashSet<String>>,
    /// Compiled regex for finding function definitions
    function_regex: Regex,
}

impl TestCache {
    pub fn new() -> Self {
        Self {
            test_functions: HashMap::new(),
            function_regex: Regex::new(r"^\s*def\s+(\w+)\s*\(").unwrap(),
        }
    }
    
    /// Build cache from test directories
    pub fn build_from_directories(project_root: &Path, test_directories: &[String]) -> Arc<Self> {
        let mut cache = Self::new();
        
        // Find all test files in parallel
        let test_files: Vec<PathBuf> = test_directories
            .par_iter()
            .flat_map(|dir_name| {
                let test_dir = project_root.join(dir_name);
                if !test_dir.exists() {
                    return vec![];
                }
                
                WalkDir::new(&test_dir)
                    .into_iter()
                    .filter_map(Result::ok)
                    .filter(|entry| {
                        entry.path().extension()
                            .and_then(|s| s.to_str()) == Some("py")
                    })
                    .map(|entry| entry.path().to_path_buf())
                    .collect::<Vec<_>>()
            })
            .collect();
        
        // Parse test files in parallel
        let function_maps: Vec<(PathBuf, HashSet<String>)> = test_files
            .par_iter()
            .filter_map(|path| {
                if let Ok(content) = fs::read_to_string(path) {
                    let functions = cache.extract_functions(&content);
                    if !functions.is_empty() {
                        return Some((path.clone(), functions));
                    }
                }
                None
            })
            .collect();
        
        // Build the cache
        for (path, functions) in function_maps {
            cache.test_functions.insert(path, functions);
        }
        
        Arc::new(cache)
    }
    
    /// Extract function names from file content
    fn extract_functions(&self, content: &str) -> HashSet<String> {
        let mut functions = HashSet::new();
        
        for line in content.lines() {
            if let Some(captures) = self.function_regex.captures(line) {
                if let Some(func_name) = captures.get(1) {
                    functions.insert(func_name.as_str().to_string());
                }
            }
        }
        
        functions
    }
    
    /// Check if a test exists for the given function
    pub fn has_test_for_function(
        &self,
        function_name: &str,
        source_path: &Path,
        class_name: Option<&str>,
    ) -> bool {
        // Generate test name patterns
        let mut test_patterns = vec![
            format!("test_{}", function_name),
            format!("test_e2e_{}", function_name),
        ];
        
        if let Some(class) = class_name {
            test_patterns.push(format!("test_{}_{}", class.to_lowercase(), function_name));
            test_patterns.push(format!("test_{}_{}", class, function_name));
        }
        
        // Get module name for file matching
        let module_name = source_path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("");
        
        // Check cached test files
        for (test_path, functions) in &self.test_functions {
            // Check if this test file might be for our module
            let file_name = test_path.file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            
            if !file_name.contains(module_name) && !file_name.starts_with("test_") {
                continue;
            }
            
            // Check if any test pattern exists in this file
            for pattern in &test_patterns {
                if functions.contains(pattern) {
                    return true;
                }
            }
        }
        
        false
    }
}