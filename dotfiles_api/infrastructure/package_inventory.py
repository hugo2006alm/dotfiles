from pathlib import Path


class PackageInventory:
    """Read pacman's local inventory without commands, logs or filesystem mutation."""

    def __init__(self, root=Path("/var/lib/pacman/local")):
        self.root = root

    def names(self):
        names = set()
        for path in self.root.glob("*/desc"):
            lines = path.read_text(encoding="utf-8").splitlines()
            if "%NAME%" in lines:
                index = lines.index("%NAME%") + 1
                if index < len(lines):
                    names.add(lines[index])
        return names
