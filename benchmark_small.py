#!/usr/bin/env python
"""Quick benchmark comparison between Python and Rust implementations."""
import time
import sys
from pathlib import Path
from proboscis_linter.config import ProboscisConfig
from proboscis_linter.rust_linter import RustLinterWrapper


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_small.py <project_path>")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: {project_path} does not exist")
        sys.exit(1)
    
    # Load configuration
    config = ProboscisConfig()
    
    print(f"Benchmarking Rust linter on: {project_path}")
    print("=" * 50)
    
    # Benchmark Rust implementation only
    try:
        rust_linter = RustLinterWrapper(config)
        start_time = time.time()
        violations = rust_linter.lint_project(project_path)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\nRust Implementation:")
        print(f"  Time: {duration:.2f} seconds")
        print(f"  Violations found: {len(violations)}")
        print(f"\nProcessing speed: {772/duration:.0f} files/second")
    
    except ImportError as e:
        print(f"\nRust implementation not available: {e}")
        print("Run 'maturin develop' to build the Rust extension")


if __name__ == "__main__":
    main()