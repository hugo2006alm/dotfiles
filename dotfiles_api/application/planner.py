from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.domain.models.planned_artifact import PlannedArtifact
from dotfiles_api.domain.models.theme_plan import ThemePlan
from dotfiles_api.application.validation import ArtifactValidator


class ThemePlanner:
    """Render and inspect all outputs without writing files or starting commands."""

    def __init__(self, env: EnvironmentContext, store: ArtifactStore, generators: list, registry=None) -> None:
        self.env, self.store, self.generators = env, store, generators
        self.registry = registry

    def build(self, tokens, theme_name: str) -> ThemePlan:
        items, targets = [], set()
        for generator in self.generators:
            previous = generator.transaction.theme_name
            generator.transaction.theme_name = theme_name
            try:
                artifacts = generator.render(tokens, theme_name)
            finally:
                generator.transaction.theme_name = previous
            if self.registry:
                self.registry.validate_artifacts(generator.name, artifacts)
            for artifact in artifacts:
                path = self.store.resolve_path(artifact.artifact_id, theme_name)
                self.env.validate_output_path(path)
                if path.resolve() in targets:
                    raise ValueError(f"Duplicate generated destination: {path}")
                targets.add(path.resolve())
                if self.registry:
                    self.registry.validate_content(generator.name, path, artifact.content)
                else:
                    ArtifactValidator().validate(path, artifact.content)
                original = path.read_bytes() if path.exists() else None
                link = str(path.readlink()) if path.is_symlink() else None
                items.append(PlannedArtifact(generator.name, artifact, path, original, link))
        return ThemePlan(theme_name, tuple(items))
