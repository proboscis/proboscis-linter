# Proboscis Linter Architecture

## Overview
A Python linter that enforces coding best practices, specifically ensuring that all Python functions have corresponding test implementations.

## Core Components

### 1. AST Function Analyzer
**Protocol**: `IFunctionAnalyzer`
- **Purpose**: Parse Python source files and extract function definitions
- **Methods**:
  - `analyze_file(file_path: Path) -> List[FunctionInfo]`
  - `has_noqa_comment(function: ast.FunctionDef) -> bool`

### 2. Test Discovery Engine
**Protocol**: `ITestDiscovery`
- **Purpose**: Find corresponding test files and functions
- **Methods**:
  - `find_test_for_function(function_info: FunctionInfo, test_directories: List[Path]) -> Optional[DiscoveredTest]`
  - `get_test_directories(project_root: Path) -> List[Path]`

### 3. Linter Rule Engine
**Protocol**: `ILinterRule`
- **Purpose**: Define and execute linting rules
- **Methods**:
  - `check(function_info: FunctionInfo) -> Optional[LintViolation]`
  - `get_rule_name() -> str`

### 4. Report Generator
**Protocol**: `IReportGenerator`
- **Purpose**: Generate linting reports in various formats
- **Methods**:
  - `generate_report(violations: List[LintViolation]) -> str`
  - `get_format_name() -> str`

## Data Models

### FunctionInfo
- `name: str` - Function name
- `file_path: Path` - Source file path
- `line_number: int` - Line number where function is defined
- `module_path: str` - Fully qualified module path
- `has_noqa: bool` - Whether function has #noqa PL*** comment

### DiscoveredTest
- `test_name: str` - Test function name
- `file_path: Path` - Test file path
- `test_type: Literal['unit', 'e2e', 'integration']` - Type of test

### LintViolation
- `rule_name: str` - Name of the violated rule
- `function_info: FunctionInfo` - Function that violated the rule
- `message: str` - Violation message
- `severity: Literal['error', 'warning']` - Severity level

## Workflow

1. **File Discovery**: Scan project for Python files
2. **Function Analysis**: Parse files using AST to extract function definitions
3. **Test Mapping**: For each function, attempt to find corresponding tests
4. **Rule Execution**: Apply linting rules to check for violations
5. **Report Generation**: Generate report of all violations

## Configuration

### Config Structure
- `test_directories: List[str]` - Directories to search for tests (default: ['test', 'tests'])
- `test_patterns: List[str]` - Patterns for test discovery
- `exclude_patterns: List[str]` - Files/directories to exclude
- `rules: Dict[str, bool]` - Enable/disable specific rules

## Entry Point

### CLI Interface
- `proboscis-lint [OPTIONS] [PATH]`
- Options:
  - `--config`: Path to configuration file
  - `--format`: Output format (text, json, junit)
  - `--fail-on-error`: Exit with non-zero code on violations