from pathlib import Path
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.reload import ReloadService

class DotfilesFacade:
    def __init__(
        self,
        env: EnvironmentContext,
        exec_ctx: ExecutionContext,
        install_service: InstallService,
        theme_service: ThemeService,
        reload_service: ReloadService,
        linker: Linker
    ) -> None:
        self._env = env
        self._exec = exec_ctx
        self._install_service = install_service
        self._theme_service = theme_service
        self._reload_service = reload_service
        self._linker = linker

    def apply_profile(self, profile: Profile) -> None:
        self._install_service.install_profile(profile)

    def apply_theme(self, theme_name: str) -> None:
        self._theme_service.apply_theme(theme_name)

    def link(self) -> None:
        self._linker.link(self._env.dotfiles_dir, self._env.home_dir)

    def reload(self) -> None:
        self._reload_service.reload_all()

    def apply_all(self, profile: Profile, theme_name: str) -> None:
        self.apply_profile(profile)
        self.link()
        self.apply_theme(theme_name)
