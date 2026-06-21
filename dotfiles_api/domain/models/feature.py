from dataclasses import dataclass

@dataclass(frozen=True)
class Feature:
    name: str
    packages: list[str]
    capabilities: list[str]
