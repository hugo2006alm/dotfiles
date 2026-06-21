from dataclasses import dataclass

@dataclass(frozen=True)
class ColorTokens:
    colors: dict[str, str]
