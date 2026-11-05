import hashlib
import os
import stat
import shutil
import tempfile
import hashlib
import json
from pathlib import Path

from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.infrastructure.safe_file import read_regular_file
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

    @staticmethod
    def source_digest(env, style, rendered):
        snapshot = ThemeStyler(env, None, None, None)._source_snapshot()
        inputs = {"source:" + name: digest.hex() for name, digest in snapshot.items()}
        inputs["stylesheet"] = style.source
        mappings = dict(style.input_paths)
        for artifact_id in style.inputs:
            item = rendered[artifact_id]
            name = mappings.get(artifact_id, item.path.name)
            inputs["generated:" + artifact_id + ":" + name] = hashlib.sha256(item.artifact.content.encode()).hexdigest()
        return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()

    def _source_snapshot(self):
        root = self.env.source_home
        if not root.is_dir() or root.is_symlink():
            raise ValueError(f"Unsafe stylesheet source directory: {root}")
        snapshot = {}
        def fail_walk(error):
            raise error
        for parent, directories, files in os.walk(root, followlinks=False, onerror=fail_walk):
            for name in directories + files:
                path = Path(parent) / name
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode):
                    raise ValueError(f"Stylesheet source may not contain symlinks: {path}")
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    raise ValueError(f"Unsupported stylesheet source: {path}")
                if stat.S_ISREG(mode):
                    snapshot[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).digest()
        return snapshot

    def compile(self, plan):
        if self.execution.dry_run:
            raise RuntimeError("Stylesheet compilation cannot run during dry-run")
        before = self._source_snapshot()
        rendered = {item.artifact.artifact_id: item for item in plan.artifacts}
        items = list(plan.artifacts)
        for spec in self.registry.specs:
            for style in spec.stylesheets:
                with tempfile.TemporaryDirectory(prefix="shade-raid-style-") as temp:
                    directory = Path(temp) / "home"
                    shutil.copytree(self.env.source_home, directory, symlinks=True)
                    if self._source_snapshot() != before:
                        raise RuntimeError("Stylesheet sources changed during compilation")
                    scratch_source = directory / style.source
                    mappings = dict(style.input_paths)
                    targets = set()
                    for artifact_id in style.inputs:
                        item = rendered[artifact_id]
                        relative = Path(mappings.get(artifact_id, item.path.name))
                        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                            raise ValueError(f"Unsafe stylesheet input path: {relative}")
                        target = scratch_source.parent / relative
                        if target == scratch_source or target in targets:
                            raise ValueError(f"Conflicting stylesheet input: {relative}")
                        targets.add(target)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(item.artifact.content, encoding="utf-8")
                    output = Path(temp) / "compiled.css"
                    self.execution.execute(["sassc", str(scratch_source), str(output)],
                                           step=f"compile:{spec.id}")
                    fingerprint = self.source_digest(self.env, style, rendered)
                    payload = output.read_text(encoding="utf-8")
                    digest = hashlib.sha256(payload.encode()).hexdigest()
                    content = f"/* shade-raid-source: {fingerprint} */\n/* shade-raid-content: {digest} */\n" + payload
                path = self.store.resolve_path(style.output, plan.theme_name)
                self.env.validate_output_path(path)
                ArtifactValidator().validate(path, content)
                original = read_regular_file(path)
                link = str(path.readlink()) if path.is_symlink() else None
                items.append(PlannedArtifact(spec.id, GeneratedArtifact(style.output, content), path, original, link))
        if self._source_snapshot() != before:
            raise RuntimeError("Stylesheet sources changed during compilation")
        return ThemePlan(plan.theme_name, tuple(items), tuple(sorted(before.items())))

    def verify_sources(self, plan):
        if plan.source_snapshot is None or tuple(sorted(self._source_snapshot().items())) != plan.source_snapshot:
            raise RuntimeError("Stylesheet sources changed after compilation")
