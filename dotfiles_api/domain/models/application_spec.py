from dataclasses import dataclass
from typing import Callable, Literal

from dotfiles_api.domain.models.output_spec import OutputSpec
from dotfiles_api.domain.models.stylesheet_spec import StylesheetSpec


@dataclass(frozen=True)
class ApplicationSpec:
    """Static application contract consumed by composition, planning and installation."""

    id: str
    packages: tuple[str, ...] = ()
    package_sources: tuple[tuple[str, str], ...] = ()
    dependencies: tuple[str, ...] = ()  # Installation dependencies.
    runtime_dependencies: tuple[str, ...] = ()
    runtime_executables: tuple[str, ...] = ()
    generator: type | None = None
    outputs: tuple[OutputSpec, ...] = ()
    stylesheets: tuple[StylesheetSpec, ...] = ()
    validator: Callable | None = None
    reload_factory: Callable | None = None
    reload_strategy: Literal["none", "application", "systemd-user-reload", "systemd-user-restart"] = "none"
    user_unit: str | None = None
    required: bool = True
    profiles: tuple[str, ...] = ("desktop",)
    capabilities: tuple[str, ...] = ()
