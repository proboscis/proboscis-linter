#!/usr/bin/env python
"""Benchmark comparison between Python and Rust implementations."""
import time
import sys
from pathlib import Path
from proboscis_linter.config import ProboscisConfig
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.rust_linter import RustLinterWrapper


def benchmark_implementation(linter, project_path, name):
    """Benchmark a linter implementation."""
    start_time = time.time()
    violations = linter.lint_project(project_path)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n{name} Implementation:")
    print(f"  Time: {duration:.2f} seconds")
    print(f"  Violations found: {len(violations)}")
    
    return duration, len(violations)


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <project_path>")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: {project_path} does not exist")
        sys.exit(1)
    
    # Load configuration
    config = ProboscisConfig()
    
    print(f"Benchmarking linter on: {project_path}")
    print("=" * 50)
    
    # Benchmark Python implementation
    python_linter = ProboscisLinter(config)
    python_time, python_violations = benchmark_implementation(
        python_linter, project_path, "Python"
    )
    
    # Benchmark Rust implementation
    try:
        rust_linter = RustLinterWrapper(config)
        rust_time, rust_violations = benchmark_implementation(
            rust_linter, project_path, "Rust"
        )
        
        # Compare results
        print("\nPerformance Comparison:")
        print("=" * 50)
        speedup = python_time / rust_time if rust_time > 0 else float('inf')
        print(f"Rust is {speedup:.2f}x faster than Python")
        
        if python_violations != rust_violations:
            print(f"\nWARNING: Different violation counts!")
            print(f"  Python: {python_violations}")
            print(f"  Rust: {rust_violations}")
    
    except ImportError as e:
        print(f"\nRust implementation not available: {e}")
        print("Run 'maturin develop' to build the Rust extension")


if __name__ == "__main__":
    main()