from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    status: str
    cleaned: Optional[str] = None
    message: Optional[str] = None

    def is_valid(self):
        return self.status == "valid"

    def is_invalid(self):
        return self.status == "invalid"