from dataclasses import dataclass


@dataclass(frozen=True)
class StylesheetSpec:
    source: str
    output: str
    inputs: tuple[str, ...]
    # Optional artifact ID to relative import path mapping, relative to source directory.
    input_paths: tuple[tuple[str, str], ...] = ()
