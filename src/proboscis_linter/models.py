from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class LintViolation(BaseModel):
    rule_name: str
    file_path: Path
    line_number: int
    function_name: str
    message: str
    severity: Literal['error', 'warning']