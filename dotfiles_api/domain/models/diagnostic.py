from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Diagnostic:
    id: str
    severity: Literal["ok", "warning", "error", "unknown"]
    message: str
    repair: tuple[str, ...] = ()
    privileged: bool = False
    evidence: str = ""
