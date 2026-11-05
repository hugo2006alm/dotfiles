from contextlib import contextmanager
import fcntl
import os
import stat


@contextmanager
def login_inputs_lock(home):
    """Shared with configuration writers; never unlink a flock inode."""
    directory = home / '.shade-raid-locks'
    if directory.exists() or directory.is_symlink():
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError(f'Unsafe login input lock directory: {directory}')
    else:
        directory.mkdir(mode=0o700)
    path = directory / 'login-inputs.lock'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ValueError(f'Unsafe login input lock: {path}')
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)
