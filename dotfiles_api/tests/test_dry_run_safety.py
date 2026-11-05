import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.infrastructure.generators.gtk import GtkGenerator
from dotfiles_api.domain.contracts import CommandResult

ROOT = Path(__file__).resolve().parents[2]


def snapshot(root):
    result = {}
    for path in root.rglob("*"):
        stat = path.lstat()
        value = os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
        result[str(path.relative_to(root))] = (stat.st_mode, stat.st_mtime_ns, value)
    return result


class TestDryRunSafety(unittest.TestCase):
    def setUp(self):
        inventory = patch("dotfiles_api.infrastructure.package_inventory.PackageInventory.names", return_value=set())
        inventory.start()
        self.addCleanup(inventory.stop)

    def test_theme_plan_lists_paths_actions_and_deferred_checks(self):
        from dotfiles_api.domain.artifacts import GeneratedArtifact
        from dotfiles_api.domain.models.planned_artifact import PlannedArtifact
        from dotfiles_api.domain.models.theme_plan import ThemePlan
        plan = ThemePlan('test', (
            PlannedArtifact('app', GeneratedArtifact('a', 'new'), Path('/home/user/new'), None),
            PlannedArtifact('app', GeneratedArtifact('b', 'new'), Path('/home/user/change'), b'old'),
            PlannedArtifact('app', GeneratedArtifact('c', 'same'), Path('/home/user/keep'), b'same'),
        ))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            plan.describe()
        text = output.getvalue()
        for expected in ('CREATE /home/user/new', 'UPDATE /home/user/change', 'KEEP /home/user/keep',
                         'app', 'deferred'):
            self.assertIn(expected, text)

    def test_papirus_folder_update_is_an_explicit_reload_effect(self):
        import inspect
        from dotfiles_api.infrastructure.reloadables.gsettings import GsettingsReloadable
        self.assertIn("loader", inspect.signature(GsettingsReloadable).parameters)
        executor, store, loader = Mock(), Mock(), Mock()
        executor.execute.return_value = CommandResult("", "", 0)
        store.get_active_theme.return_value = "shade-raid-dark"
        loader.load.return_value.colors.colors = {"papirus_folder_color": "violet"}
        with patch("shutil.which", return_value="/fake/papirus-folders"):
            GsettingsReloadable(ExecutionContext(False, executor), store, loader).reload()
        commands = [call.args[0] for call in executor.execute.call_args_list]
        self.assertIn(["papirus-folders", "-C", "violet"], commands)

    def test_setup_dry_run_can_plan_from_fresh_home_without_linking(self):
        from dotfiles_api.presentation.cli import main
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            with patch.dict(os.environ, {"DOTFILES_DIR": str(ROOT),
                                        "XDG_RUNTIME_DIR": str(home / ".runtime"),
                                        "XDG_STATE_HOME": str(home / ".state")}), \
                    patch("os.geteuid", return_value=1000), patch("pathlib.Path.home", return_value=home), \
                    patch("subprocess.Popen") as process, \
                    patch("threading.Thread.start") as thread, contextlib.redirect_stdout(io.StringIO()) as output:
                main(["setup", "--dry-run"])
            self.assertIn("PLAN: theme shade-raid", output.getvalue())
            self.assertEqual(list(home.iterdir()), [])
            process.assert_not_called()
            thread.assert_not_called()

    def test_cli_workflows_leave_files_state_and_processes_unchanged(self):
        from dotfiles_api.presentation.cli import main
        cases = [
            ["configure", "--theme", "shade-raid-dark"], ["toggle"], ["apply-all"],
            ["setup", "--github"], ["link"], ["reload"],
            ["action", "preview", "next"], ["action", "record"],
            ["action", "session"], ["action", "portal"],
        ]
        for words in cases:
            with self.subTest(command=words), tempfile.TemporaryDirectory() as temp:
                home = Path(temp)
                themes = home / ".config/themes"
                shutil.copytree(ROOT / "home/.config/themes", themes)
                (themes / "current").write_text("shade-raid")
                before = snapshot(home)
                variables = {"DOTFILES_DIR": str(ROOT), "XDG_STATE_HOME": str(home / ".local/state"),
                             "XDG_RUNTIME_DIR": str(home / ".runtime")}
                with patch.dict(os.environ, variables), patch("os.geteuid", return_value=1000), patch("pathlib.Path.home", return_value=home), \
                        patch("subprocess.Popen") as process, \
                        patch("threading.Thread.start") as thread, \
                        patch("dotfiles_api.infrastructure.executor.SystemCommandExecutor.execute") as executor, \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    main(["--dry-run", *words])
                self.assertEqual(snapshot(home), before)
                process.assert_not_called()
                thread.assert_not_called()
                executor.assert_not_called()

    def test_dry_run_error_preserves_every_file(self):
        from dotfiles_api.presentation.cli import main
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            theme = home / ".config/themes/broken"
            theme.mkdir(parents=True)
            (theme / "colors.toml").write_text("invalid = [")
            before = snapshot(home)
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(home / ".runtime"),
                                         "XDG_STATE_HOME": str(home / ".local/state")}), \
                    patch("pathlib.Path.home", return_value=home), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    main(["configure", "--theme", "broken", "--dry-run"])
            self.assertEqual(snapshot(home), before)

    def test_gtk_render_never_starts_papirus_process(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            themes = env.home_dir / ".config/themes"
            shutil.copytree(ROOT / "home/.config/themes", themes)
            tokens = ThemeLoader(env).load("shade-raid")
            with patch("shutil.which", return_value="/fake/papirus-folders"), patch("subprocess.Popen") as process:
                GtkGenerator().render(tokens, "shade-raid")
            process.assert_not_called()

    def test_recorder_dry_run_preserves_running_pid_file(self):
        from dotfiles_api.infrastructure.actions.recorder import RecorderAction
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            recorder = RecorderAction(ExecutionContext(True, Mock()), env)
            recorder._pid_file.parent.mkdir(parents=True)
            recorder._pid_file.write_text("12345")
            before = snapshot(env.home_dir)
            with contextlib.redirect_stdout(io.StringIO()):
                recorder.execute([])
            self.assertEqual(snapshot(env.home_dir), before)
