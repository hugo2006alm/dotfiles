import json
import os
import shutil
import uuid
from pathlib import Path


class HomeMigration:
    """Unfold legacy repository links and retain recovery data."""

    def __init__(self, source: Path, target: Path) -> None:
        self.source, self.target = source.absolute(), target.absolute()
        self.package = self.source / "home"
        self.legacy = self.source / "templates/legacy"
        self.links = []
        self.backup = None
        self._changed = []
        self._missing = []
        if not self.package.is_dir():
            raise ValueError(f"Missing declarative package: {self.package}")
        names = {p.name for p in self.package.iterdir()}
        if self.legacy.is_dir():
            names.update(p.name for p in self.legacy.iterdir())
        for name in sorted(names):
            self._inspect(Path(name))
        for item in self.package.rglob("*"):
            destination = self.target / item.relative_to(self.package)
            if not destination.exists() and not destination.is_symlink():
                self._missing.append(destination)

    def _inspect(self, relative: Path) -> None:
        destination = self.target / relative
        static, fallback = self.package / relative, self.legacy / relative
        if destination.is_symlink():
            raw = os.readlink(destination)
            resolved = Path(os.path.abspath(destination.parent / raw))
            if resolved == self.source / relative or (static.is_dir() and resolved == static):
                directory = static.is_dir() or resolved.is_dir() or fallback.is_dir()
                self.links.append((destination, raw, resolved, directory))
            elif static.is_dir() or fallback.is_dir():
                raise ValueError(f"Refusing unmanaged directory symlink: {destination}")
            return
        if not destination.is_dir():
            return
        names = set()
        for candidate in (static, fallback):
            if candidate.is_dir():
                names.update(p.name for p in candidate.iterdir())
        if len(relative.parts) >= 2:
            names.update(p.name for p in destination.iterdir())
        for name in sorted(names):
            self._inspect(relative / name)

    def _copy_unmanaged(self, source: Path, destination: Path, relative: Path) -> None:
        if not source.is_dir():
            return
        for child in source.iterdir():
            target = destination / child.name
            child_relative = relative / child.name
            static = self.package / child_relative
            if static.exists() or static.is_symlink():
                if child.is_dir() and not child.is_symlink() and static.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    self._copy_unmanaged(child, target, child_relative)
                continue
            if target.exists() or target.is_symlink():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if child.is_symlink():
                target.symlink_to(os.readlink(child))
            elif child.is_dir():
                shutil.copytree(child, target, symlinks=True)
            else:
                shutil.copy2(child, target)

    def __enter__(self):
        if not self.links:
            return self
        # Keep recovery data outside old folds, including ~/.local itself.
        base = self.target / ".shade-raid-backups"
        if base.is_symlink() or base.resolve().is_relative_to(self.source.resolve()):
            raise ValueError(f"Unsafe migration backup directory: {base}")
        self.backup = base / ("stow-" + uuid.uuid4().hex)
        self.backup.mkdir(parents=True, mode=0o700)
        manifest = []
        for destination, raw, old, directory in self.links:
            relative = destination.relative_to(self.target)
            saved = self.backup / "contents" / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            if old.is_dir():
                shutil.copytree(old, saved, symlinks=True)
            elif old.is_file():
                shutil.copy2(old, saved)
            manifest.append({"path": str(relative), "link": raw, "directory": directory})
        metadata = self.backup / "manifest.json"
        metadata.write_text(json.dumps(manifest, indent=2))
        metadata.chmod(0o600)
        print(f"Stow migration backup: {self.backup}")
        try:
            for destination, raw, old, directory in self.links:
                relative = destination.relative_to(self.target)
                destination.unlink()
                self._changed.append((destination, raw))
                if directory:
                    destination.mkdir()
                    self._copy_unmanaged(old, destination, relative)
                    self._copy_unmanaged(self.legacy / relative, destination, relative)
                elif not (self.package / relative).exists():
                    material = old if old.is_file() else self.legacy / relative
                    if not material.is_file():
                        raise ValueError(f"Cannot recover legacy generated file: {destination}")
                    shutil.copy2(material, destination)
        except BaseException:
            self._restore()
            raise
        return self

    def _restore(self) -> None:
        roots = [path for path, _ in self._changed]
        for path in sorted(self._missing, key=lambda item: len(item.parts), reverse=True):
            if any(path == root or path.is_relative_to(root) for root in roots):
                continue
            if path.is_symlink():
                expected = self.package / path.relative_to(self.target)
                if path.resolve() == expected.resolve():
                    path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        failures = []
        for destination, raw in reversed(self._changed):
            try:
                if destination.is_symlink() or destination.is_file():
                    destination.unlink()
                elif destination.exists():
                    shutil.rmtree(destination)
                destination.symlink_to(raw)
            except OSError as error:
                failures.append(f"{destination}: {error}")
        if failures:
            raise RuntimeError(f"Migration recovery incomplete; backup {self.backup}: " + "; ".join(failures))

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self._restore()
        return False
