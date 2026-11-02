from dotfiles_api.application.package_catalog import PACKAGE_SOURCES
from dotfiles_api.application.application_registry import ApplicationRegistry


class PackageRegistry:
    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
        custom_mapping = mapping if mapping is not None else {}
        # The central catalog is the source of truth for known packages.
        # Caller-provided mappings still work for unknown/custom package names.
        self._mapping = {**custom_mapping, **PACKAGE_SOURCES, **ApplicationRegistry(APPLICATIONS).package_sources()}

    def resolve_source(self, package: str) -> str:
        return self._mapping.get(package, "pacman")
