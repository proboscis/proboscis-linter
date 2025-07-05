from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel


class LintViolation(BaseModel):
    rule_name: str
    file_path: Path
    line_number: int
    function_name: str
    message: str
    severity: Literal['error', 'warning']
    fix_type: Optional[str] = None
    fix_content: Optional[str] = None
    fix_line: Optional[int] = None