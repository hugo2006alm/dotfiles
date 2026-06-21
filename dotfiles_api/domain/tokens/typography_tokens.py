from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class TypographyTokens:
    typography: dict[str, Any]
