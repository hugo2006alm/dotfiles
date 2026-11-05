from dotfiles_api.application.package_catalog import PACKAGE_SOURCES
from dotfiles_api.application.application_registry import ApplicationRegistry


class PackageRegistry:
    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
        custom_mapping = mapping if mapping is not None else {}
        if any(source not in {"pacman", "yay"} for source in custom_mapping.values()):
            raise ValueError("Invalid package source override")
        known = {package for spec in APPLICATIONS for package in spec.packages}
        catalog = ApplicationRegistry(APPLICATIONS, {key: value for key, value in custom_mapping.items() if key in known}).package_sources()
        for package, source in PACKAGE_SOURCES.items():
            if package in catalog and catalog[package] != source and package not in custom_mapping:
                raise ValueError(f"Conflicting package sources for {package}: {source}, {catalog[package]}")
        self._mapping = {**PACKAGE_SOURCES, **catalog, **custom_mapping}

    def resolve_source(self, package: str) -> str:
        return self._mapping.get(package, "pacman")
