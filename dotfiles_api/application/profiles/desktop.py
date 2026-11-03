from dotfiles_api.application.hardware import COMMON_GRAPHICS_PACKAGES
from dotfiles_api.domain.models.profile import Profile


def build_desktop_profile(
    optional_packages: list[str] | None = None,
    graphics_packages: list[str] | None = None,
) -> Profile:
    selected_graphics = list(graphics_packages or COMMON_GRAPHICS_PACKAGES)

    from dotfiles_api.application.profiles.software import SoftwareProfileResolver
    return SoftwareProfileResolver().resolve(["desktop"], optional_packages, selected_graphics)
