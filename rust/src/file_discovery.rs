use regex::Regex;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Convert glob pattern to regex
pub fn glob_to_regex(pattern: &str) -> Option<Regex> {
    let mut regex_pattern = String::new();
    let chars: Vec<char> = pattern.chars().collect();
    let mut i = 0;
    
    while i < chars.len() {
        match chars[i] {
            '*' => {
                if i + 1 < chars.len() && chars[i + 1] == '*' {
                    regex_pattern.push_str(".*");
                    i += 2;
                    if i < chars.len() && chars[i] == '/' {
                        i += 1;
                    }
                } else {
                    regex_pattern.push_str("[^/]*");
                    i += 1;
                }
            }
            '?' => {
                regex_pattern.push_str("[^/]");
                i += 1;
            }
            '.' | '+' | '^' | '$' | '(' | ')' | '[' | ']' | '{' | '}' | '|' | '\\' => {
                regex_pattern.push('\\');
                regex_pattern.push(chars[i]);
                i += 1;
            }
            _ => {
                regex_pattern.push(chars[i]);
                i += 1;
            }
        }
    }
    
    Regex::new(&regex_pattern).ok()
}

/// Find all Python files in a directory, excluding test and virtual environment directories
pub fn find_python_files(root: &Path, exclude_patterns: &[String]) -> Vec<PathBuf> {
    let exclude_regexes: Vec<Regex> = exclude_patterns
        .iter()
        .filter_map(|p| glob_to_regex(p))
        .collect();
    
    let files: Vec<PathBuf> = WalkDir::new(root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| {
            let path = entry.path();
            
            // Skip if it's not a Python file
            if !path.is_file() || path.extension().and_then(|s| s.to_str()) != Some("py") {
                return false;
            }
            
            // Skip test directories and hidden/virtual environment directories
            if path.components().any(|c| {
                c.as_os_str().to_str().map(|s| 
                    s == "test" || s == "tests" || s == "__pycache__" || 
                    s == ".venv" || s == "venv" || s == "env" || s == ".env" ||
                    (s.starts_with('.') && s != "." && s != "..")
                ).unwrap_or(false)
            }) {
                return false;
            }
            
            // Check exclude patterns
            let path_str = path.to_str().unwrap_or("");
            if exclude_regexes.iter().any(|re| re.is_match(path_str)) {
                return false;
            }
            
            true
        })
        .map(|entry| entry.path().to_path_buf())
        .collect();
    
    files
}