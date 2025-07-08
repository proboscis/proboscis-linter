use rayon::prelude::*;
use regex::Regex;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use walkdir::WalkDir;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum TestType {
    Unit,
    Integration,
    E2E,
    General,
}

impl TestType {
    pub fn from_path(path: &Path) -> Self {
        let path_str = path.to_string_lossy();
        if path_str.contains("/e2e/") || path_str.contains("\\e2e\\") {
            TestType::E2E
        } else if path_str.contains("/integration/") || path_str.contains("\\integration\\") {
            TestType::Integration
        } else if path_str.contains("/unit/") || path_str.contains("\\unit\\") {
            TestType::Unit
        } else {
            TestType::General
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            TestType::Unit => "unit",
            TestType::Integration => "integration",
            TestType::E2E => "e2e",
            TestType::General => "general",
        }
    }
}

/// Information about a test file
#[derive(Debug)]
struct TestFileInfo {
    path: PathBuf,
    test_type: TestType,
    functions: HashSet<String>,
}

/// Cache for test file contents and patterns
pub struct TestCache {
    /// Map from test file path to test file info
    test_files: HashMap<PathBuf, TestFileInfo>,
    /// Compiled regex for finding function definitions
    function_regex: Regex,
}

impl TestCache {
    pub fn new() -> Self {
        Self {
            test_files: HashMap::new(),
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
                    .filter(|entry| entry.path().extension().and_then(|s| s.to_str()) == Some("py"))
                    .map(|entry| entry.path().to_path_buf())
                    .collect::<Vec<_>>()
            })
            .collect();

        // Parse test files in parallel
        let file_infos: Vec<TestFileInfo> = test_files
            .par_iter()
            .filter_map(|path| {
                if let Ok(content) = fs::read_to_string(path) {
                    let functions = cache.extract_functions(&content);
                    if !functions.is_empty() {
                        let test_type = TestType::from_path(path);
                        return Some(TestFileInfo {
                            path: path.clone(),
                            test_type,
                            functions,
                        });
                    }
                }
                None
            })
            .collect();

        // Build the cache
        for info in file_infos {
            cache.test_files.insert(info.path.clone(), info);
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
        // Get module name for file matching
        let module_name = source_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("");

        // Check cached test files
        for (_, info) in &self.test_files {
            // Check if this test file might be for our module
            let file_name = info.path.file_name().and_then(|s| s.to_str()).unwrap_or("");

            if !file_name.contains(module_name) && !file_name.starts_with("test_") {
                continue;
            }

            // Generate test patterns based on test type
            let test_patterns =
                self.generate_test_patterns(function_name, class_name, &info.test_type);

            // Check if any test pattern exists in this file
            for pattern in &test_patterns {
                if info.functions.contains(pattern) {
                    return true;
                }
            }
        }

        false
    }

    /// Check if a test of a specific type exists for the given function
    pub fn has_test_for_function_of_type(
        &self,
        function_name: &str,
        source_path: &Path,
        class_name: Option<&str>,
        test_type: &TestType,
        module_path: &str,
        project_root: &Path,
    ) -> bool {
        // Get module name for file matching
        let module_name = source_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("");

        // Check cached test files of the specific type
        for (test_path, info) in &self.test_files {
            // Skip if not the right test type
            if &info.test_type != test_type && info.test_type != TestType::General {
                continue;
            }

            // Check if this test file is in the right directory structure
            // For pkg.mod1.submod, we expect tests in test/unit/pkg/mod1/test_submod.py
            if !module_path.is_empty() {
                let expected_test_dir =
                    self.get_expected_test_path(module_path, &info.test_type, project_root);
                let test_dir = test_path.parent().unwrap_or(Path::new(""));

                // Check if the test file is in the expected directory
                if !test_dir.ends_with(&expected_test_dir) {
                    // Also check if it's in the parent directory with the right name
                    let file_name = test_path.file_name().and_then(|s| s.to_str()).unwrap_or("");

                    if !file_name.contains(module_name) && !file_name.starts_with("test_") {
                        continue;
                    }
                }
            }

            // Generate test patterns based on test type
            let test_patterns = self.generate_test_patterns(function_name, class_name, test_type);

            // Check if any test pattern exists in this file
            for pattern in &test_patterns {
                if info.functions.contains(pattern) {
                    return true;
                }
            }
        }

        false
    }

    /// Get the single canonical test pattern for a function
    pub fn get_canonical_test_pattern(
        &self,
        function_name: &str,
        class_name: Option<&str>,
        test_type: &TestType,
    ) -> String {
        // Single deterministic pattern for each case
        if let Some(class) = class_name {
            match test_type {
                TestType::Unit => format!("test_{}_{}", class, function_name),
                TestType::Integration => format!("test_{}_{}", class, function_name),
                TestType::E2E => format!("test_{}_{}", class, function_name),
                TestType::General => format!("test_{}_{}", class, function_name),
            }
        } else {
            // For standalone functions
            format!("test_{}", function_name)
        }
    }

    /// Generate test patterns based on function name, class, and test type
    pub fn generate_test_patterns(
        &self,
        function_name: &str,
        class_name: Option<&str>,
        test_type: &TestType,
    ) -> Vec<String> {
        let mut patterns = vec![];

        // If this is a class method, use different naming patterns
        if let Some(class) = class_name {
            match test_type {
                TestType::Unit => {
                    // Primary pattern: test_ClassName_method_name
                    patterns.push(format!("test_{}_{}", class, function_name));
                    patterns.push(format!("test_{}_{}", class.to_lowercase(), function_name));
                    patterns.push(format!("test_unit_{}_{}", class, function_name));
                    // Fallback patterns
                    patterns.push(format!("test_{}", function_name));
                }
                TestType::Integration => {
                    patterns.push(format!("test_integration_{}_{}", class, function_name));
                    patterns.push(format!("test_int_{}_{}", class, function_name));
                    patterns.push(format!("test_{}_{}", class, function_name));
                    // Fallback
                    patterns.push(format!("test_integration_{}", function_name));
                }
                TestType::E2E => {
                    patterns.push(format!("test_e2e_{}_{}", class, function_name));
                    patterns.push(format!("test_end_to_end_{}_{}", class, function_name));
                    patterns.push(format!("test_{}_{}", class, function_name));
                    // Fallback
                    patterns.push(format!("test_e2e_{}", function_name));
                }
                TestType::General => {
                    patterns.push(format!("test_{}_{}", class, function_name));
                    patterns.push(format!("test_{}_{}", class.to_lowercase(), function_name));
                    patterns.push(format!("test_unit_{}_{}", class, function_name));
                    patterns.push(format!("test_integration_{}_{}", class, function_name));
                    patterns.push(format!("test_e2e_{}_{}", class, function_name));
                    // Fallback
                    patterns.push(format!("test_{}", function_name));
                }
            }
        } else {
            // For standalone functions
            match test_type {
                TestType::Unit => {
                    patterns.push(format!("test_{}", function_name));
                    patterns.push(format!("test_unit_{}", function_name));
                }
                TestType::Integration => {
                    patterns.push(format!("test_integration_{}", function_name));
                    patterns.push(format!("test_int_{}", function_name));
                    patterns.push(format!("test_{}", function_name));
                }
                TestType::E2E => {
                    patterns.push(format!("test_e2e_{}", function_name));
                    patterns.push(format!("test_end_to_end_{}", function_name));
                    patterns.push(format!("test_{}", function_name));
                }
                TestType::General => {
                    patterns.push(format!("test_{}", function_name));
                    patterns.push(format!("test_e2e_{}", function_name));
                    patterns.push(format!("test_integration_{}", function_name));
                    patterns.push(format!("test_unit_{}", function_name));
                }
            }
        }

        patterns
    }

    /// Get expected test path for a module
    pub fn get_expected_test_path(
        &self,
        module_path: &str,
        test_type: &TestType,
        project_root: &Path,
    ) -> PathBuf {
        // Split module path into components
        let components: Vec<&str> = module_path.split('.').collect();

        // Base test directory based on test type
        let base_dir = match test_type {
            TestType::Unit => "test/unit",
            TestType::Integration => "test/integration",
            TestType::E2E => "test/e2e",
            TestType::General => "test",
        };

        // Build the expected path
        let mut path = PathBuf::from(base_dir);
        if components.len() > 1 {
            // Add all but the last component as directories
            for component in &components[..components.len() - 1] {
                path.push(component);
            }
        }

        path
    }

    /// Get the absolute path where the test file should be located
    pub fn get_expected_test_file_path(
        &self,
        module_path: &str,
        source_file_name: &str,
        test_type: &TestType,
        project_root: &Path,
    ) -> PathBuf {
        let test_dir = self.get_expected_test_path(module_path, test_type, project_root);

        // Convert source file name to test file name (e.g., bitflyer.py -> test_bitflyer.py)
        let test_file_name = if source_file_name.ends_with(".py") {
            format!("test_{}", source_file_name)
        } else {
            format!("test_{}.py", source_file_name)
        };

        // Return absolute path
        project_root.join(test_dir).join(test_file_name)
    }

    /// Get information about where tests are found (for error messages)
    pub fn get_test_locations(&self) -> HashMap<TestType, Vec<String>> {
        let mut locations: HashMap<TestType, Vec<String>> = HashMap::new();

        for (_, info) in &self.test_files {
            let dir = info
                .path
                .parent()
                .and_then(|p| p.file_name())
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();

            locations
                .entry(info.test_type.clone())
                .or_insert_with(Vec::new)
                .push(dir);
        }

        // Deduplicate
        for (_, dirs) in locations.iter_mut() {
            dirs.sort();
            dirs.dedup();
        }

        locations
    }
}
