from pathlib import Path
import re


class PackageInventory:
    """Read installed package names; missing or invalid database is an error."""

    def __init__(self, root=Path("/var/lib/pacman/local")):
        self.root = root

    def names(self):
        if not self.root.is_dir():
            raise RuntimeError(f"Pacman local database is unavailable: {self.root}")
        names = set()
        try:
            version = self.root / "ALPM_DB_VERSION"
            if version.is_symlink() or not version.read_text(encoding="ascii").strip().isdigit():
                raise ValueError(f"invalid database version: {version}")
            for directory in self.root.iterdir():
                if not directory.is_dir():
                    continue
                if directory.is_symlink():
                    raise ValueError(f"linked package database entry: {directory}")
                path = directory / "desc"
                if path.is_symlink():
                    raise ValueError(f"linked package metadata: {path}")
                lines = path.read_text(encoding="utf-8").splitlines()
                if lines.count("%NAME%") != 1:
                    raise ValueError(f"missing or duplicated NAME: {path}")
                index = lines.index("%NAME%") + 1
                if index >= len(lines) or not re.fullmatch(r"[a-zA-Z0-9@_+][a-zA-Z0-9@_.+-]*", lines[index]):
                    raise ValueError(f"invalid NAME: {path}")
                if lines.count("%VERSION%") != 1:
                    raise ValueError(f"missing or duplicated VERSION: {path}")
                version_index = lines.index("%VERSION%") + 1
                if version_index >= len(lines) or not lines[version_index] or lines[version_index].startswith("%"):
                    raise ValueError(f"invalid VERSION: {path}")
                name = lines[index]
                if name in names:
                    raise ValueError(f"duplicated package: {name}")
                names.add(name)
        except (OSError, UnicodeError, ValueError) as error:
            raise RuntimeError(f"Pacman local database is unreadable or corrupt: {error}") from error
        return names
