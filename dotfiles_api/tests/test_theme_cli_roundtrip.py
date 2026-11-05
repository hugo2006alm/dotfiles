import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
import re
from pathlib import Path
from unittest.mock import patch

from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.tests.test_dry_run_safety import snapshot

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("stow") and shutil.which("sassc"), "Requires real GNU Stow and sassc")
class TestThemeCliRoundtrip(unittest.TestCase):
    def test_real_cli_applies_light_dark_and_rollback_without_changing_source(self):
        from dotfiles_api.presentation.cli import main
        before_source = snapshot(ROOT / "home")
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(ROOT, home)
            variables = {"DOTFILES_DIR": str(ROOT), "XDG_STATE_HOME": str(home / ".state"),
                         "XDG_RUNTIME_DIR": str(home / ".runtime")}
            real_execute = SystemCommandExecutor().execute
            def execute(args, cwd=None):
                return real_execute(args, cwd) if args[0] == "sassc" else CommandResult("", "", 0)
            with patch.dict(os.environ, variables), patch("pathlib.Path.home", return_value=home), \
                    patch.object(SystemCommandExecutor, "execute", side_effect=execute) as executor, \
                    patch("subprocess.Popen", wraps=subprocess.Popen) as process, contextlib.redirect_stdout(io.StringIO()):
                main(["configure", "--theme", "shade-raid"])
                light = (home / ".config/ghostty/colors.conf").read_bytes()
                def refreshes():
                    return [call for call in executor.call_args_list if call.args[0][0] != "sassc"]
                calls = len(refreshes())
                main(["configure", "--theme", "shade-raid"])
                self.assertEqual(len(refreshes()), calls, "Unchanged theme should not refresh applications or wallpaper")
                main(["configure", "--theme", "shade-raid-dark"])
                self.assertNotEqual((home / ".config/ghostty/colors.conf").read_bytes(), light)
                before_preview = snapshot(home)
                main(["rollback", "--dry-run"])
                self.assertEqual(snapshot(home), before_preview)
                main(["rollback"])
                self.assertEqual((home / ".config/ghostty/colors.conf").read_bytes(), light)
                self.assertEqual((home / ".state/shade-raid/active-theme").read_text().strip(), "shade-raid")
                css = home / ".config/waybar/style.css"
                expected_css = css.read_bytes()
                css.unlink()
                (home / ".state/shade-raid/installation.json").write_text('{"version":2,"requested_profiles":["desktop"],"explicit_packages":[]}')
                before_diagnosis = snapshot(home)
                with contextlib.redirect_stdout(io.StringIO()) as diagnosis:
                    main(["repair", "--plan"])
                self.assertEqual(snapshot(home), before_diagnosis)
                plan_id = re.search(r"REPAIR PLAN ([0-9a-f]{64})", diagnosis.getvalue()).group(1)
                with patch("dotfiles_api.infrastructure.actions.wallpaper.WallpaperAction.execute") as wallpaper:
                    main(["repair", "--apply", "--plan-id", plan_id])
                wallpaper.assert_not_called()
                self.assertEqual(css.read_bytes(), expected_css)
                self.assertTrue(all(call.args[0][0] == "sassc" for call in process.call_args_list))
            for app in ("waybar", "wlogout", "swayosd"):
                self.assertTrue((home / ".config" / app / "style.css").is_file())
            self.assertTrue((home / ".config/walker/themes/shade-raid/style.css").is_file())
        self.assertEqual(snapshot(ROOT / "home"), before_source)
