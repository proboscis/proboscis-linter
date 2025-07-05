use regex::Regex;
use std::collections::HashSet;

/// Parse noqa comments and return the set of suppressed rules
/// Supports formats:
///   - #noqa PL001
///   - #noqa: PL001
///   - #noqa PL001, PL002
///   - #noqa: PL001, PL002
pub fn parse_noqa_rules(line: &str) -> HashSet<String> {
    let mut rules = HashSet::new();
    
    // Match #noqa with optional colon, followed by rule codes
    // This regex captures everything after #noqa or #noqa:
    let noqa_regex = Regex::new(r"#\s*noqa(?:\s*:)?\s*(.*)").unwrap();
    
    if let Some(captures) = noqa_regex.captures(line) {
        if let Some(rules_str) = captures.get(1) {
            // Split by comma and/or whitespace
            let rules_part = rules_str.as_str();
            
            // Split by comma first, then trim whitespace
            for rule in rules_part.split(',') {
                let trimmed = rule.trim();
                // Only add if it matches pattern PLxxx
                if trimmed.starts_with("PL") && trimmed.len() > 2 {
                    rules.insert(trimmed.to_string());
                }
            }
        }
    }
    
    rules
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_noqa_single_rule() {
        let rules = parse_noqa_rules("def foo():  #noqa PL001");
        assert_eq!(rules.len(), 1);
        assert!(rules.contains("PL001"));
    }
    
    #[test]
    fn test_parse_noqa_with_colon() {
        let rules = parse_noqa_rules("def foo():  #noqa: PL001");
        assert_eq!(rules.len(), 1);
        assert!(rules.contains("PL001"));
    }
    
    #[test]
    fn test_parse_noqa_multiple_rules() {
        let rules = parse_noqa_rules("def foo():  #noqa PL001, PL002");
        assert_eq!(rules.len(), 2);
        assert!(rules.contains("PL001"));
        assert!(rules.contains("PL002"));
    }
    
    #[test]
    fn test_parse_noqa_multiple_rules_with_colon() {
        let rules = parse_noqa_rules("def foo():  #noqa: PL001, PL002, PL003");
        assert_eq!(rules.len(), 3);
        assert!(rules.contains("PL001"));
        assert!(rules.contains("PL002"));
        assert!(rules.contains("PL003"));
    }
    
    #[test]
    fn test_parse_noqa_with_extra_spaces() {
        let rules = parse_noqa_rules("def foo():  # noqa : PL001 , PL002");
        assert_eq!(rules.len(), 2);
        assert!(rules.contains("PL001"));
        assert!(rules.contains("PL002"));
    }
    
    #[test]
    fn test_parse_noqa_no_rules() {
        let rules = parse_noqa_rules("def foo():  #noqa");
        assert_eq!(rules.len(), 0);
    }
    
    #[test]
    fn test_parse_no_noqa() {
        let rules = parse_noqa_rules("def foo():  # just a comment");
        assert_eq!(rules.len(), 0);
    }
}