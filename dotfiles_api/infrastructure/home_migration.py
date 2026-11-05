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
        self.seeds = self.source / "seeds"
        self.links = []
        self.backup = None
        self._changed = []
        self._missing = []
        if not self.package.is_dir():
            raise ValueError(f"Missing declarative package: {self.package}")
        names = {p.name for p in self.package.iterdir()}
        if self.legacy.is_dir():
            names.update(p.name for p in self.legacy.iterdir())
        if self.seeds.is_dir():
            names.update(p.name for p in self.seeds.iterdir())
        for name in sorted(names):
            self._inspect(Path(name))
        for item in self.package.rglob("*"):
            destination = self.target / item.relative_to(self.package)
            if not destination.exists() and not destination.is_symlink():
                self._missing.append(destination)

    def _inspect(self, relative: Path) -> None:
        destination = self.target / relative
        static, fallback, seed = self.package / relative, self.legacy / relative, self.seeds / relative
        if destination.is_symlink():
            raw = os.readlink(destination)
            resolved = Path(os.path.abspath(destination.parent / raw))
            if resolved in (self.source / relative, static, seed):
                directory = static.is_dir() or resolved.is_dir() or fallback.is_dir() or seed.is_dir()
                self.links.append((destination, raw, resolved, directory))
            elif static.is_dir() or fallback.is_dir() or seed.is_dir():
                raise ValueError(f"Refusing unmanaged directory symlink: {destination}")
            return
        if not destination.is_dir():
            return
        names = set()
        for candidate in (static, fallback, seed):
            if candidate.is_dir():
                names.update(p.name for p in candidate.iterdir())
        if len(relative.parts) >= 2:
            names.update(p.name for p in destination.iterdir())
        for name in sorted(names):
            self._inspect(relative / name)

    def _validate_overlap(self, source: Path, relative: Path) -> None:
        """Refuse to replace old content unless it matches the declarative file."""
        static = self.package / relative
        if not (static.exists() or static.is_symlink()):
            return
        if source.is_symlink() or static.is_symlink():
            if not (source.is_symlink() and static.is_symlink() and
                    os.path.realpath(source) == os.path.realpath(static)):
                raise ValueError(f"Legacy content conflicts with declarative file: {source}")
        elif source.is_dir() and static.is_dir():
            for child in source.iterdir():
                self._validate_overlap(child, relative / child.name)
        elif not (source.is_file() and static.is_file() and
                  source.read_bytes() == static.read_bytes()):
            raise ValueError(f"Legacy content conflicts with declarative file: {source}")

    def _copy_unmanaged(self, source: Path, destination: Path, relative: Path) -> None:
        if not source.is_dir():
            return
        for child in source.iterdir():
            target = destination / child.name
            child_relative = relative / child.name
            static = self.package / child_relative
            if child.is_dir() and not child.is_symlink():
                if static.exists() and not static.is_dir():
                    continue
                created = not target.exists()
                if created:
                    target.mkdir(mode=child.stat().st_mode & 0o777)
                    target.chmod(child.stat().st_mode & 0o777)
                self._copy_unmanaged(child, target, child_relative)
                if created:
                    shutil.copystat(child, target, follow_symlinks=False)
            elif static.exists() or static.is_symlink() or target.exists() or target.is_symlink():
                continue
            elif child.is_symlink():
                raw = os.readlink(child)
                if not os.path.isabs(raw):
                    resolved = os.path.abspath(child.parent / raw)
                    raw = os.path.relpath(resolved, target.parent)
                target.symlink_to(raw)
            elif child.is_file():
                shutil.copy2(child, target)
            else:
                raise ValueError(f"Unsupported legacy file: {child}")

    def __enter__(self):
        if not self.links:
            return self
        # Inspect every overlap before unlinking any fold.
        for destination, raw, old, directory in self.links:
            self._validate_overlap(old, destination.relative_to(self.target))
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
                    destination.mkdir(mode=old.stat().st_mode & 0o777 if old.is_dir() else 0o700)
                    if old.is_dir():
                        destination.chmod(old.stat().st_mode & 0o777)
                    self._copy_unmanaged(old, destination, relative)
                    self._copy_unmanaged(self.legacy / relative, destination, relative)
                elif not (self.package / relative).exists():
                    material = next((item for item in (old, self.legacy / relative, self.seeds / relative)
                                     if item.is_file()), old)
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
                if destination.exists() or destination.is_symlink():
                    saved = self.backup / "failed-contents" / destination.relative_to(self.target)
                    saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    os.replace(destination, saved)
                destination.symlink_to(raw)
            except OSError as error:
                failures.append(f"{destination}: {error}")
        if failures:
            raise RuntimeError(f"Migration recovery incomplete; backup {self.backup}: " + "; ".join(failures))

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self._restore()
        return False
