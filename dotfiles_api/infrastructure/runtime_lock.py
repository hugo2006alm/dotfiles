import fcntl
import os
import stat
import threading
from pathlib import Path


class RuntimeLock:
    """Reentrant per thread, serialized across processes; never unlink lock files."""

    _local = threading.local()

    def __init__(self, path: Path, blocking: bool = True) -> None:
        self.path = Path(os.path.abspath(path))
        self.blocking = blocking
        self.key = (os.getpid(), str(self.path))

    def __enter__(self):
        held = getattr(self._local, "held", None)
        if held is None:
            held = self._local.held = {}
        if self.key in held:
            held[self.key][1] += 1
            return self
        if self.path.parent.is_symlink():
            raise ValueError(f"Refusing linked lock directory: {self.path.parent}")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Unsafe lock file: {self.path}")
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if self.blocking else fcntl.LOCK_NB))
        except BaseException:
            os.close(fd)
            raise
        held[self.key] = [fd, 1]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        held = self._local.held
        entry = held[self.key]
        entry[1] -= 1
        if entry[1] == 0:
            fcntl.flock(entry[0], fcntl.LOCK_UN)
            os.close(entry[0])
            del held[self.key]
        return False
