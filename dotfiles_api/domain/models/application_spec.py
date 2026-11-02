from dataclasses import dataclass
from typing import Callable

from dotfiles_api.domain.models.output_spec import OutputSpec


@dataclass(frozen=True)
class ApplicationSpec:
    """Static application contract consumed by composition, planning and installation."""

    id: str
    packages: tuple[str, ...] = ()
    package_sources: tuple[tuple[str, str], ...] = ()
    dependencies: tuple[str, ...] = ()
    generator: type | None = None
    outputs: tuple[OutputSpec, ...] = ()
    validator: Callable | None = None
    reload_factory: Callable | None = None
    reload_strategy: str = "none"
    required: bool = True
    profiles: tuple[str, ...] = ("desktop",)
    capabilities: tuple[str, ...] = ()
