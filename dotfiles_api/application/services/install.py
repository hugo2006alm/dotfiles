from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.domain.contracts.package_source import PackageSource
from dotfiles_api.domain.models.profile import Profile

class InstallService:
    def __init__(
        self,
        env: EnvironmentContext | None,
        exec_ctx: ExecutionContext | None,
        registry: PackageRegistry,
        sources: dict[str, PackageSource]
    ) -> None:
        self._env = env
        self._exec = exec_ctx
        self._registry = registry
        self._sources = sources

    def install_profile(self, profile: Profile) -> None:
        packages = profile.get_packages()
        
        grouped: dict[str, list[str]] = {}
        for package in packages:
            source_id = self._registry.resolve_source(package)
            if source_id not in grouped:
                grouped[source_id] = []
            grouped[source_id].append(package)
            
        for source_id, pkgs in grouped.items():
            if source_id not in self._sources:
                raise RuntimeError(f"Package source '{source_id}' is not configured: {', '.join(pkgs)}")
            source = self._sources[source_id]
            if not source.is_available() and not (self._exec and self._exec.dry_run):
                raise RuntimeError(f"Package source '{source_id}' is unavailable: {', '.join(pkgs)}")
        # Check every source before installing any group.
        for source_id, pkgs in grouped.items():
            self._sources[source_id].install(pkgs)
