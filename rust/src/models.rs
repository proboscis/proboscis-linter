use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct LintViolation {
    #[pyo3(get)]
    pub rule_name: String,
    #[pyo3(get)]
    pub file_path: String,
    #[pyo3(get)]
    pub line_number: usize,
    #[pyo3(get)]
    pub function_name: String,
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub severity: String,
}