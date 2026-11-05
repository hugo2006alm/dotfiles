from pathlib import Path
from contextlib import nullcontext
from dotfiles_api.infrastructure.login_lock import login_inputs_lock
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.reload import ReloadService

from dotfiles_api.application.services.setup import SetupService


class DotfilesFacade:
    def __init__(
        self,
        env: EnvironmentContext,
        exec_ctx: ExecutionContext,
        install_service: InstallService,
        theme_service: ThemeService,
        reload_service: ReloadService,
        linker: Linker,
        setup_service: SetupService | None = None
    ) -> None:
        self._env = env
        self._exec = exec_ctx
        self._install_service = install_service
        self._theme_service = theme_service
        self._reload_service = reload_service
        self._linker = linker
        self._setup_service = setup_service

    def apply_profile(self, profile: Profile) -> None:
        self._install_service.install_profile(profile)

    def apply_theme(self, theme_name: str) -> None:
        with nullcontext() if self._exec.dry_run else login_inputs_lock(self._env.home_dir):
            self._theme_service.apply_theme(theme_name)

    def link(self) -> None:
        self._linker.link(self._env.dotfiles_dir, self._env.home_dir)

    def reload(self) -> None:
        self._reload_service.reload_all()

    def setup(self, setup_github: bool, enable_ssh_server: bool = False, change_shell: bool = False, theme_name: str | None = None) -> None:
        if self._setup_service:
            with nullcontext() if self._exec.dry_run else login_inputs_lock(self._env.home_dir):
                options = {"enable_ssh_server": enable_ssh_server}
                if change_shell:
                    options["change_shell"] = True
                if theme_name is not None:
                    options["theme_name"] = theme_name
                self._setup_service.run_setup(setup_github, **options)

    def apply_all(self, profile: Profile, theme_name: str) -> None:
        self.apply_profile(profile)
        self.link()
        self.apply_theme(theme_name)
