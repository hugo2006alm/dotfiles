from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileSpec:
    id: str
    dependencies: tuple[str, ...] = ()
    description: str = ""
