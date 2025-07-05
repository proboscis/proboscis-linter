use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::Path;

/// Represents the public API of a module
#[derive(Debug, Clone)]
pub struct PublicApi {
    /// If Some, only these names are public. If None, use underscore convention.
    pub all_names: Option<HashSet<String>>,
}

impl PublicApi {
    /// Create a PublicApi that uses underscore convention
    pub fn default() -> Self {
        PublicApi { all_names: None }
    }
    
    /// Check if a function/class is public
    pub fn is_public(&self, name: &str) -> bool {
        match &self.all_names {
            Some(all_set) => all_set.contains(name),
            None => !name.starts_with('_'),
        }
    }
}

/// Extract __all__ from a Python module
pub fn extract_module_all(file_path: &Path) -> Result<PublicApi, std::io::Error> {
    let content = fs::read_to_string(file_path)?;
    
    // Look for __all__ = [...] pattern (can be multi-line)
    let all_regex = Regex::new(r"(?s)__all__\s*=\s*\[(.*?)\]").unwrap();
    
    if let Some(captures) = all_regex.captures(&content) {
        if let Some(names_str) = captures.get(1) {
            let names = parse_all_names(names_str.as_str());
            return Ok(PublicApi {
                all_names: Some(names),
            });
        }
    }
    
    // No __all__ found, use default
    Ok(PublicApi::default())
}

/// Parse names from __all__ list content
fn parse_all_names(content: &str) -> HashSet<String> {
    let mut names = HashSet::new();
    
    // Match both single and double quoted strings
    let name_regex = Regex::new(r#"['"]([^'"]+)['"]"#).unwrap();
    
    for capture in name_regex.captures_iter(content) {
        if let Some(name) = capture.get(1) {
            names.insert(name.as_str().to_string());
        }
    }
    
    names
}

/// Check if a function should be checked based on public API rules
pub fn should_check_function(
    function_name: &str,
    class_name: Option<&str>,
    public_api: &PublicApi,
    strict_mode: bool,
) -> bool {
    // Special methods are always excluded
    if function_name == "__init__" {
        return false;
    }
    
    // In strict mode, check all functions except special methods
    if strict_mode {
        return true;
    }
    
    // If function is a method, check if it's private
    if class_name.is_some() && function_name.starts_with('_') {
        return false;
    }
    
    // If no class, check module-level visibility
    if class_name.is_none() {
        return public_api.is_public(function_name);
    }
    
    // For methods, check if the class is public
    if let Some(class) = class_name {
        public_api.is_public(class)
    } else {
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_all_names() {
        let content = "'func1', 'func2', \"func3\"";
        let names = parse_all_names(content);
        assert_eq!(names.len(), 3);
        assert!(names.contains("func1"));
        assert!(names.contains("func2"));
        assert!(names.contains("func3"));
    }
    
    #[test]
    fn test_parse_all_names_multiline() {
        let content = r#"
            'func1',
            "func2",
            'func3'
        "#;
        let names = parse_all_names(content);
        assert_eq!(names.len(), 3);
    }
    
    #[test]
    fn test_parse_all_names_empty() {
        let content = "";
        let names = parse_all_names(content);
        assert_eq!(names.len(), 0);
    }
    
    #[test]
    fn test_is_public_with_all() {
        let mut names = HashSet::new();
        names.insert("public_func".to_string());
        
        let public_api = PublicApi {
            all_names: Some(names),
        };
        
        assert!(public_api.is_public("public_func"));
        assert!(!public_api.is_public("other_func"));
        assert!(!public_api.is_public("_private_func"));
    }
    
    #[test]
    fn test_is_public_without_all() {
        let public_api = PublicApi::default();
        
        assert!(public_api.is_public("public_func"));
        assert!(!public_api.is_public("_private_func"));
        assert!(!public_api.is_public("__double_underscore"));
    }
}