import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.services.login import LoginSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult


@unittest.skipUnless(os.environ.get("SHADE_RAID_DISPOSABLE_ARCH") == "1",
                     "Requires a disposable Arch container; modifies its /etc/greetd")
class TestArchLoginIntegration(unittest.TestCase):
    def test_real_installs_secure_old_files_and_leave_restorable_snapshot(self):
        self.assertEqual(os.geteuid(), 0)
        target = Path("/etc/greetd")
        target.mkdir(exist_ok=True)
        old = {"config.toml": b"[old]\nvalue = true\n", "regreet-background.jpg": b"old background"}
        for name, content in old.items():
            (target / name).write_bytes(content)
            (target / name).chmod(0o666)
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            external = home / "must-not-overwrite.css"
            external.write_text("personal stylesheet")
            if (target / "regreet.css").exists() or (target / "regreet.css").is_symlink():
                (target / "regreet.css").unlink()
            (target / "regreet.css").symlink_to(external)
            source = home / ".config/greetd"
            source.mkdir(parents=True)
            (source / "hyprland-greet.conf").write_text("exec-once = regreet\n")
            (source / "regreet.css").write_text("window { background: black; }\n")
            (source / "regreet.toml").write_text("[GTK]\napplication_prefer_dark_theme = true\n")

            def root_command(args, cwd=None):
                self.assertEqual(args[0], "sudo")
                command = args[1:]
                if command[0] == "systemctl":
                    return CommandResult("", "", 0)
                process = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
                return CommandResult(process.stdout, process.stderr, process.returncode)

            executor = Mock()
            executor.execute.side_effect = root_command
            env = EnvironmentContext(home, home / "dotfiles", "tester")
            with patch("sys.stdin.isatty", return_value=True):
                backup = LoginSetupService(ExecutionContext(False, executor), env).apply()
            self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
            self.assertEqual(external.read_text(), "personal stylesheet")
            self.assertTrue((backup / "greetd/regreet.css").is_symlink())
            for name, content in old.items():
                self.assertEqual((backup / "greetd" / name).read_bytes(), content)
            for name in (*old, "regreet.toml", "regreet.css", "hyprland-greet.conf"):
                self.assertEqual((target / name).stat().st_mode & 0o777, 0o644, name)
                self.assertEqual((target / name).stat().st_uid, 0, name)
            with patch("sys.stdin.isatty", return_value=True):
                second = LoginSetupService(ExecutionContext(False, executor), env).apply()
            self.assertNotEqual(backup, second)
            self.assertEqual((second / "greetd/config.toml").read_bytes(), (target / "config.toml").read_bytes())
