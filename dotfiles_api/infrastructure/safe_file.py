"""Read regular files without blocking on FIFOs or reading device nodes."""
import os
import stat
from pathlib import Path


def read_regular_file(path: Path) -> bytes | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode):
        try:
            info = path.stat()
        except FileNotFoundError as error:
            raise ValueError(f"Broken output symlink: {path}") from error
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Expected regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        actual = os.fstat(fd)
        if not stat.S_ISREG(actual.st_mode) or (info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino):
            raise ValueError(f"File changed during inspection: {path}")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            return stream.read()
    finally:
        if fd >= 0:
            os.close(fd)
