from pathlib import Path
import os
import stat
import tempfile
from dotfiles_api.domain.contracts import FileWriter

class SystemFileWriter(FileWriter):
    def write(self, target_path: Path, content: str) -> None:
        self.write_bytes(target_path, content.encode("utf-8"))

    def write_bytes(self, target_path: Path, content: bytes) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(target_path.stat().st_mode) if target_path.is_file() and not target_path.is_symlink() else 0o600
        fd, name = tempfile.mkstemp(prefix=".shade-raid-", dir=target_path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target_path)
            directory = os.open(target_path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)
