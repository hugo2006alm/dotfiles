from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.domain.models.profile_spec import ProfileSpec


PROFILES = (
    ProfileSpec("core", description="Shell and base utilities"),
    ProfileSpec("appearance", ("core",), "Fonts, icons and theme tooling"),
    ProfileSpec("desktop", ("core", "appearance"), "Wayland desktop"),
    ProfileSpec("daily", ("desktop",), "Browser, password manager and chat"),
    ProfileSpec("dev", ("core",), "Development tools"),
    ProfileSpec("gaming", ("desktop",), "Gaming tools"),
    ProfileSpec("ai", ("core",), "Local AI tools; review hardware requirements"),
)


class SoftwareProfileResolver:
    def __init__(self, applications=None, profiles=PROFILES):
        if applications is None:
            from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
            applications = APPLICATIONS
        self.applications = applications
        self.profiles = {profile.id: profile for profile in profiles}
        if len(self.profiles) != len(profiles):
            raise ValueError("Duplicate software profiles")

    def resolve(self, names, optional_packages=None, graphics_packages=None):
        ordered, visiting = [], set()
        def visit(name):
            if name not in self.profiles:
                raise ValueError(f"Unknown profile: {name}")
            if name in visiting:
                raise ValueError(f"Profile dependency cycle: {name}")
            if name in ordered:
                return
            visiting.add(name)
            for dependency in self.profiles[name].dependencies:
                visit(dependency)
            visiting.remove(name)
            ordered.append(name)
        requested = ["desktop"] if names is None else list(names)
        for name in requested:
            visit(name)
        features = [Feature(spec.id, list(spec.packages), list(spec.capabilities))
                    for spec in self.applications if set(spec.profiles) & set(ordered)]
        if "desktop" in ordered and graphics_packages:
            features.append(Feature("graphics", list(graphics_packages), ["graphics"]))
        selected = tuple(dict.fromkeys(optional_packages or []))
        if selected:
            features.append(Feature("optional", list(selected), []))
        return Profile("+".join(requested), features, tuple(ordered), selected, tuple(dict.fromkeys(requested)))
