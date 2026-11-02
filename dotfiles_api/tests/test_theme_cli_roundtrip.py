import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.tests.test_dry_run_safety import snapshot

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("stow"), "Requires real GNU Stow")
class TestThemeCliRoundtrip(unittest.TestCase):
    def test_real_cli_applies_light_dark_and_rollback_without_changing_source(self):
        from dotfiles_api.presentation.cli import main
        before_source = snapshot(ROOT / "home")
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(ROOT, home)
            variables = {"DOTFILES_DIR": str(ROOT), "XDG_STATE_HOME": str(home / ".state"),
                         "XDG_RUNTIME_DIR": str(home / ".runtime")}
            with patch.dict(os.environ, variables), patch("pathlib.Path.home", return_value=home), \
                    patch.object(SystemCommandExecutor, "execute", return_value=CommandResult("", "", 0)) as executor, \
                    patch("subprocess.Popen") as process, contextlib.redirect_stdout(io.StringIO()):
                main(["configure", "--theme", "shade-raid"])
                light = (home / ".config/ghostty/colors.conf").read_bytes()
                calls = executor.call_count
                main(["configure", "--theme", "shade-raid"])
                self.assertEqual(executor.call_count, calls, "Unchanged theme should not refresh applications or wallpaper")
                main(["configure", "--theme", "shade-raid-dark"])
                self.assertNotEqual((home / ".config/ghostty/colors.conf").read_bytes(), light)
                before_preview = snapshot(home)
                main(["rollback", "--dry-run"])
                self.assertEqual(snapshot(home), before_preview)
                main(["rollback"])
                self.assertEqual((home / ".config/ghostty/colors.conf").read_bytes(), light)
                self.assertEqual((home / ".state/shade-raid/active-theme").read_text().strip(), "shade-raid")
                process.assert_not_called()
        self.assertEqual(snapshot(ROOT / "home"), before_source)
