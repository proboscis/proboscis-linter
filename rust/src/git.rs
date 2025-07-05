use std::path::{Path, PathBuf};
use std::process::Command;

/// Get files with unstaged changes or staged changes (diff)
pub fn get_changed_files(project_root: &Path) -> Vec<PathBuf> {
    let mut changed_files = Vec::new();
    
    // Get staged files (in the index)
    if let Ok(output) = Command::new("git")
        .current_dir(project_root)
        .args(&["diff", "--cached", "--name-only"])
        .output()
    {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.ends_with(".py") {
                    changed_files.push(project_root.join(line));
                }
            }
        }
    }
    
    // Get unstaged files (modified in working directory)
    if let Ok(output) = Command::new("git")
        .current_dir(project_root)
        .args(&["diff", "--name-only"])
        .output()
    {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.ends_with(".py") {
                    let path = project_root.join(line);
                    // Only add if not already in the list
                    if !changed_files.contains(&path) {
                        changed_files.push(path);
                    }
                }
            }
        }
    }
    
    // Get untracked files
    if let Ok(output) = Command::new("git")
        .current_dir(project_root)
        .args(&["ls-files", "--others", "--exclude-standard"])
        .output()
    {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.ends_with(".py") {
                    let path = project_root.join(line);
                    // Only add if not already in the list
                    if !changed_files.contains(&path) {
                        changed_files.push(path);
                    }
                }
            }
        }
    }
    
    changed_files
}

/// Check if we're in a git repository
pub fn is_git_repository(path: &Path) -> bool {
    Command::new("git")
        .current_dir(path)
        .args(&["rev-parse", "--git-dir"])
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}