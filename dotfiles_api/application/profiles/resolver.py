from collections.abc import Callable

from dotfiles_api.application.hardware import detect_graphics_packages
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.application.profiles.software import SoftwareProfileResolver


class DesktopProfileResolver:
    """Resolve hardware once and reuse it across installation entry points."""

    def __init__(self, graphics_detector: Callable[[], list[str]] = detect_graphics_packages) -> None:
        self._detect = graphics_detector
        self._graphics: list[str] | None = None

    def resolve(self, optional_packages: list[str] | None = None) -> Profile:
        return self.resolve_profiles(["desktop"], optional_packages)

    def resolve_profiles(self, profiles, optional_packages=None) -> Profile:
        if self._graphics is None:
            self._graphics = list(self._detect())
        return SoftwareProfileResolver().resolve(profiles, optional_packages, self._graphics)
