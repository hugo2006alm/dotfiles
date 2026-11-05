from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.domain.contracts.package_source import PackageSource
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.application.installation_error import InstallationError

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
                raise RuntimeError(f"Source preflight failed; no installation commands attempted. Package source '{source_id}' is not configured: {', '.join(pkgs)}")
            source = self._sources[source_id]
            if not (self._exec and self._exec.dry_run) and not source.is_available():
                raise RuntimeError(f"Source preflight failed; no installation commands attempted. Package source '{source_id}' is unavailable: {', '.join(pkgs)}")
        # Check every source before installing any group.
        completed = []
        for source_id, pkgs in grouped.items():
            try:
                self._sources[source_id].install(pkgs)
            except Exception as error:
                raise InstallationError(tuple(completed), source_id) from error
            completed.append((source_id, tuple(pkgs)))
