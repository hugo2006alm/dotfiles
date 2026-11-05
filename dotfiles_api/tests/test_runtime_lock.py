import tempfile
import threading
import unittest
from pathlib import Path
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock


class TestRuntimeLock(unittest.TestCase):
    def test_lock_is_reentrant_and_keeps_same_inode_between_uses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runtime/configure.lock"
            with RuntimeLock(path):
                inode = path.stat().st_ino
                with RuntimeLock(path):
                    self.assertEqual(path.stat().st_ino, inode)
            with RuntimeLock(path):
                self.assertEqual(path.stat().st_ino, inode)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_other_thread_cannot_take_held_lock_nonblocking(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runtime/configure.lock"
            errors = []
            def attempt():
                try:
                    with RuntimeLock(path, blocking=False):
                        errors.append("unexpected acquisition")
                except BlockingIOError:
                    errors.append("blocked")
            with RuntimeLock(path):
                thread = threading.Thread(target=attempt)
                thread.start()
                thread.join(timeout=3)
                self.assertFalse(thread.is_alive())
            self.assertEqual(errors, ["blocked"])

    def test_symbolic_lock_file_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            personal = root / "personal"
            personal.write_text("keep")
            (root / "lock").symlink_to(personal)
            with self.assertRaises(OSError):
                with RuntimeLock(root / "lock"):
                    pass
            self.assertEqual(personal.read_text(), "keep")
