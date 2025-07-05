# Performance Optimizations

The proboscis-linter has been optimized for speed through several key improvements:

## 1. Test File Caching
- **Before**: Every function would walk the test directory and read files repeatedly
- **After**: All test files are read once and cached at the start
- **Impact**: Eliminates redundant file I/O operations

## 2. Parallel Test File Parsing
- Test files are parsed in parallel using rayon
- Function names are extracted and stored in a HashMap for O(1) lookups

## 3. Compiled Regex Patterns
- **Before**: Regex patterns compiled for every file
- **After**: Patterns compiled once and reused
- **Impact**: Reduces regex compilation overhead

## 4. Optimized Test Discovery Algorithm
```rust
// Old approach - O(n * m * p) where:
// n = number of functions
// m = number of test files  
// p = average file size
for each function:
    for each test_dir:
        walk directory
        for each test file:
            read file
            search for pattern

// New approach - O(n + m * p)
// Build cache once:
for each test_dir:
    walk directory (parallel)
    read all test files (parallel)
    extract all function names

// Then for each function - O(1) lookup:
check if test exists in cache
```

## 5. Architecture Benefits

### Memory Efficiency
- Test cache uses Arc for zero-copy sharing across threads
- HashSet for function names provides fast lookups

### CPU Efficiency
- Parallel processing of both source files and test files
- Regex operations minimized through caching

## Performance Results

Testing on proboscis-ema (772 Python files):
- **Before optimization**: ~10-14 seconds
- **After optimization**: ~1.5 seconds
- **Speedup**: 6-9x faster

The optimizations make the linter practical for use in:
- Git pre-commit hooks
- CI/CD pipelines
- Editor integrations
- Real-time feedback during development