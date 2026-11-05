import contextlib
import io
import json
import time
import sys
import os
import shutil
import subprocess
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
                main(["action", "preview", "next"])
                before_preview = snapshot(home)
                main(["rollback", "--dry-run"])
                self.assertEqual(snapshot(home), before_preview)
                main(["rollback"])
                self.assertEqual((home / ".config/ghostty/colors.conf").read_bytes(), light)
                self.assertEqual((home / ".state/shade-raid/active-theme").read_text().strip(), "shade-raid")
                self.assertTrue(all(call.args[0][0] == "sassc" for call in process.call_args_list))
            for app in ("waybar", "wlogout", "swayosd"):
                self.assertTrue((home / ".config" / app / "style.css").is_file())
            self.assertTrue((home / ".config/walker/themes/shade-raid/style.css").is_file())
        self.assertEqual(snapshot(ROOT / "home"), before_source)

    def test_real_cli_apply_preview_then_rollback_restores_previous_theme(self):
        from dotfiles_api.presentation.cli import main
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(ROOT, home)
            variables = {"DOTFILES_DIR": str(ROOT), "XDG_STATE_HOME": str(home / ".state"),
                         "XDG_RUNTIME_DIR": str(home / ".runtime")}
            with patch.dict(os.environ, variables), patch("pathlib.Path.home", return_value=home), \
                    patch.object(SystemCommandExecutor, "execute", return_value=CommandResult("", "", 0)), \
                    contextlib.redirect_stdout(io.StringIO()):
                main(["configure", "--theme", "shade-raid"])
                light = (home / ".config/swaync/config.json").read_bytes()
                main(["configure", "--theme", "shade-raid-dark"])
                dark = (home / ".config/swaync/config.json").read_bytes()
                main(["action", "preview", "next"])
                preview = (home / ".config/swaync/config.json").read_bytes()
                self.assertNotEqual(preview, dark, "preview must visibly update SwayNC selection")
                sway_config = home / ".config/swaync/config.json"
                sway_config.write_text("personal edit")
                with self.assertRaisesRegex(RuntimeError, "changed since application"):
                    main(["rollback"])
                self.assertEqual(sway_config.read_text(), "personal edit")
                sway_config.write_bytes(preview)
                main(["action", "preview", "next"])
                self.assertNotEqual((home / ".state/shade-raid/preview-theme").read_text().strip(),
                                    "shade-raid", "repeated preview must advance from the current selection")
                main(["action", "preview", "prev"])
                # Emulate power loss after some prepared preview writes reached disk.
                previews = home / ".state/shade-raid/preview-transactions"
                active = []
                for manifest_path in previews.glob("*/manifest.json"):
                    data = json.loads(manifest_path.read_text())
                    if data["status"] == "committed":
                        active.append((manifest_path, data))
                self.assertEqual(len(active), 1)
                manifest_path, manifest = active[0]
                manifest["status"] = "prepared"
                manifest_path.write_text(json.dumps(manifest))
                record = next(record for record in manifest["files"] if record["artifact_id"] == "swaync-config")
                if record["exists"] and record["link"] is None:
                    Path(record["path"]).write_bytes((manifest_path.parent / "backups" / record["backup"]).read_bytes())
                before_dry_run = snapshot(home)
                main(["rollback", "--dry-run"])
                self.assertEqual(snapshot(home), before_dry_run)
                main(["rollback"])
                self.assertEqual((home / ".config/swaync/config.json").read_bytes(), light)
                self.assertEqual((home / ".state/shade-raid/active-theme").read_text().strip(), "shade-raid")

    def test_preview_waits_for_configure_lock_across_processes(self):
        from dotfiles_api.context.environment import EnvironmentContext
        from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            themes = home / ".config/themes"
            for name in ("alpha", "beta"):
                (themes / name).mkdir(parents=True)
                (themes / name / "colors.toml").write_text("")
            bin_dir = home / "bin"
            bin_dir.mkdir()
            binary = bin_dir / "swaync-client"
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            env = EnvironmentContext(home, ROOT, "test", state_home=home / ".state", runtime_home=home / ".runtime")
            variables = {**os.environ, "PYTHONPATH": str(ROOT), "HOME": str(home),
                         "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}
            script = (
                'from pathlib import Path; from dotfiles_api.context.environment import EnvironmentContext; '
                'from dotfiles_api.context.execution import ExecutionContext; from dotfiles_api.infrastructure.executor import SystemCommandExecutor; '
                'from dotfiles_api.infrastructure.actions.preview import PreviewAction; '
                f'e=EnvironmentContext(Path({str(home)!r}),Path({str(ROOT)!r}),"test",state_home=Path({str(home / ".state")!r}),runtime_home=Path({str(home / ".runtime")!r})); '
                'PreviewAction(ExecutionContext(False,SystemCommandExecutor()),e).execute(["next"])'
            )
            with RuntimeLock(env.lock_dir / "configure.lock"):
                process = subprocess.Popen([sys.executable, "-c", script], cwd=ROOT, env=variables,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                time.sleep(.3)
                self.assertIsNone(process.poll(), "preview must wait until configure releases its lock")
                self.assertFalse(env.preview_file.exists())
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stdout + stderr)
            self.assertEqual(env.preview_file.read_text(), "beta")
