from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OutputSpec:
    id: str
    path: str
    scope: Literal["home", "state"] = "home"
