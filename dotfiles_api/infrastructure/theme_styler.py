import shutil
import tempfile
from pathlib import Path

from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.domain.models.planned_artifact import PlannedArtifact
from dotfiles_api.domain.models.theme_plan import ThemePlan


class ThemeStyler:
    """Compile in private scratch space; only the coordinator installs final CSS."""

    def __init__(self, env, registry, store, execution):
        self.env, self.registry, self.store, self.execution = env, registry, store, execution

    def describe(self):
        count = sum(len(spec.stylesheets) for spec in self.registry.specs)
        print(f"  Compile {count} stylesheets before installation (deferred in dry-run)")

    def compile(self, plan):
        if self.execution.dry_run:
            raise RuntimeError("Stylesheet compilation cannot run during dry-run")
        rendered = {item.artifact.artifact_id: item for item in plan.artifacts}
        items = list(plan.artifacts)
        for spec in self.registry.specs:
            for style in spec.stylesheets:
                source = self.env.source_home / style.source
                with tempfile.TemporaryDirectory(prefix="shade-raid-style-") as temp:
                    directory = Path(temp) / "source"
                    shutil.copytree(source.parent, directory)
                    for artifact_id in style.inputs:
                        item = rendered[artifact_id]
                        (directory / item.path.name).write_text(item.artifact.content, encoding="utf-8")
                    output = Path(temp) / "compiled.css"
                    self.execution.execute(["sassc", str(directory / source.name), str(output)],
                                           step=f"compile:{spec.id}")
                    content = output.read_text(encoding="utf-8")
                path = self.store.resolve_path(style.output, plan.theme_name)
                self.env.validate_output_path(path)
                ArtifactValidator().validate(path, content)
                original = path.read_bytes() if path.exists() else None
                link = str(path.readlink()) if path.is_symlink() else None
                items.append(PlannedArtifact(spec.id, GeneratedArtifact(style.output, content), path, original, link))
        return ThemePlan(plan.theme_name, tuple(items))
