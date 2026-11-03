import re
from dotfiles_api.domain.models.installation_plan import InstallationPlan


class InstallationPlanner:
    def __init__(self, registry, sources, inventory):
        self.registry, self.sources, self.inventory = registry, sources, inventory

    def build(self, profile, dry_run=False):
        installed, grouped = self.inventory(), {}
        packages = profile.get_packages()
        for package in packages:
            if not re.fullmatch(r"[a-zA-Z0-9@_+][a-zA-Z0-9@_.+-]*", package):
                raise ValueError(f"Invalid package name: {package!r}")
            if package in installed:
                continue
            source_id = self.registry.resolve_source(package)
            official = self.sources.get("pacman")
            if (not dry_run and source_id != "pacman" and official and hasattr(official, "contains")
                    and official.is_available() and official.contains(package)):
                source_id = "pacman"
            if source_id not in self.sources:
                raise RuntimeError(f"Package source '{source_id}' is not configured: {package}")
            source = self.sources[source_id]
            if not dry_run:
                if not source.is_available():
                    raise RuntimeError(f"Package source '{source_id}' is unavailable: {package}")
                if hasattr(source, "contains") and not source.contains(package):
                    raise RuntimeError(f"Package {package} is unavailable in {source_id}; refresh/review repositories before retrying")
            grouped.setdefault(source_id, []).append(package)
        return InstallationPlan(tuple((source, tuple(items)) for source, items in grouped.items()),
                                tuple(package for package in packages if package in installed))
