from dataclasses import dataclass


@dataclass(frozen=True)
class StylesheetSpec:
    source: str
    output: str
    inputs: tuple[str, ...]
