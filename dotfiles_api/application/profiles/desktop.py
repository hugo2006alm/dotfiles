from dotfiles_api.application.hardware import COMMON_GRAPHICS_PACKAGES
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile


def build_desktop_profile(
    optional_packages: list[str] | None = None,
    graphics_packages: list[str] | None = None,
) -> Profile:
    selected_graphics = list(graphics_packages or COMMON_GRAPHICS_PACKAGES)

    from dotfiles_api.application.application_registry import ApplicationRegistry
    from dotfiles_api.infrastructure.application_catalog import APPLICATIONS

    registry = ApplicationRegistry(APPLICATIONS)
    features = [Feature(name=spec.id, packages=list(spec.packages), capabilities=list(spec.capabilities))
                for spec in registry.installation_specs(["desktop"], optional_packages or [])]
    features.append(Feature(name="graphics", packages=selected_graphics, capabilities=["graphics"]))

    selected = list(optional_packages or [])
    if selected:
        features.append(Feature(name="optional", packages=selected, capabilities=[]))

    return Profile(name="desktop", features=features)
