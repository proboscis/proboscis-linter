#!/usr/bin/env python
"""Debug script to compare files found by Python vs Rust implementations."""
import sys
from pathlib import Path
from proboscis_linter.config import ProboscisConfig
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.rust_linter import RustLinterWrapper


def main():
    project_path = Path(".")
    config = ProboscisConfig()
    
    # Python implementation
    python_linter = ProboscisLinter(config)
    python_files = python_linter._find_python_files(project_path)
    
    print("Python implementation found files:")
    for f in sorted(python_files):
        print(f"  {f}")
    
    print(f"\nTotal: {len(python_files)} files")
    
    # For Rust, we'll need to check by running lint and seeing what files it processes
    print("\nRunning Rust implementation to see which files it processes...")
    rust_linter = RustLinterWrapper(config)
    violations = rust_linter.lint_project(project_path)
    
    # Get unique file paths from violations
    rust_files = set()
    for v in violations:
        rust_files.add(v.file_path)
    
    print(f"\nRust found violations in {len(rust_files)} files")
    
    # Compare
    python_set = set(str(f) for f in python_files)
    rust_set = rust_files
    
    only_python = python_set - rust_set
    if only_python:
        print(f"\nFiles only processed by Python ({len(only_python)}):")
        for f in sorted(only_python):
            print(f"  {f}")


if __name__ == "__main__":
    main()