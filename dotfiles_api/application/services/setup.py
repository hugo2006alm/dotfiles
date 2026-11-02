import sys
from collections.abc import Callable

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.hardware import detect_graphics_packages
from dotfiles_api.application.package_catalog import OPTIONAL_PACKAGES
from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.optional_packages import OptionalPackageSelectionService
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.application.services.extras import ExtrasSetupService


class SetupService:
    def __init__(
        self,
        env: EnvironmentContext,
        exec_ctx: ExecutionContext,
        install_service: InstallService,
        linker: Linker,
        theme_service: ThemeService,
        services_service: ServicesSetupService,
        user_service: UserSetupService,
        extras_service: ExtrasSetupService,
        optional_package_selector: OptionalPackageSelectionService | None = None,
        graphics_package_detector: Callable[[], list[str]] = detect_graphics_packages,
        profile_resolver: DesktopProfileResolver | None = None,
    ) -> None:
        self._env = env
        self._exec = exec_ctx
        self._install_service = install_service
        self._linker = linker
        self._theme_service = theme_service
        self._services = services_service
        self._user = user_service
        self._extras = extras_service
        self._optional_package_selector = optional_package_selector or OptionalPackageSelectionService()
        self._profile_resolver = profile_resolver or DesktopProfileResolver(graphics_package_detector)

    def run_setup(self, setup_github: bool = False, enable_ssh_server: bool = False) -> None:
        selected_optional_packages: list[str] = []
        if sys.stdin.isatty():
            selected_optional_packages = self._optional_package_selector.select(OPTIONAL_PACKAGES)

        desktop_profile = self._profile_resolver.resolve(selected_optional_packages)

        self._install_service.install_profile(desktop_profile)
        self._linker.link(self._env.dotfiles_dir, self._env.home_dir)
        if enable_ssh_server:
            self._services.setup_services(enable_ssh_server=True)
        else:
            self._services.setup_services()
        self._user.setup_user(setup_github=setup_github)
        self._theme_service.apply_theme("shade-raid")
        self._extras.setup_extras()
