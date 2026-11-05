import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.reloadables.regreet import ReGreetReloadable


class TestLoginSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = EnvironmentContext(self.home, self.home / "dotfiles", "tester")
        self.executor = Mock()
        self.executor.execute.return_value = CommandResult("", "", 0)
        self.ctx = ExecutionContext(False, self.executor)

    def test_normal_setup_does_not_change_login_or_sudoers(self):
        ServicesSetupService(self.ctx, self.env).setup_services()
        for call in self.executor.execute.call_args_list:
            command = " ".join(call.args[0])
            self.assertNotIn("greetd", command)
            self.assertNotIn("sudoers", command)

    def test_theme_reload_never_requests_privileges(self):
        ReGreetReloadable(self.ctx, self.env).reload()
        self.executor.execute.assert_not_called()

    def test_wallpaper_never_writes_login_background_even_if_old_permissions_allow_it(self):
        from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction

        wallpapers = self.home / "wallpapers/shade-raid"
        wallpapers.mkdir(parents=True)
        (wallpapers / "image.jpg").write_bytes(b"image")
        exists = Path.exists
        with patch("os.access", return_value=True), patch("shutil.which", return_value="/usr/bin/convert"), \
                patch.object(Path, "exists", lambda path: str(path).startswith("/etc/greetd") or exists(path)):
            WallpaperAction(self.ctx, self.env).execute([])
        for call in self.executor.execute.call_args_list:
            self.assertNotIn("/etc/greetd", " ".join(call.args[0]))

    def test_login_requires_interactive_session_before_any_command(self):
        from dotfiles_api.application.services.login import LoginSetupService

        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "interactive"):
                LoginSetupService(self.ctx, self.env).apply()
        self.executor.execute.assert_not_called()

    def test_optional_spotify_customization_never_makes_system_apps_world_writable(self):
        from dotfiles_api.application.services.extras import ExtrasSetupService

        prefs = self.home / ".config/spotify/prefs"
        prefs.parent.mkdir(parents=True)
        prefs.write_text("prefs")
        with patch("shutil.which", return_value="/usr/bin/spotify"), patch("os.access", return_value=False):
            ExtrasSetupService(self.ctx, self.env).setup_extras()
        self.executor.execute.assert_not_called()

    def test_login_validates_all_inputs_before_privileged_changes(self):
        from dotfiles_api.application.services.login import LoginSetupService

        source = self.home / ".config/greetd"
        source.mkdir(parents=True)
        (source / "regreet.toml").write_text("invalid = [")
        (source / "regreet.css").write_text("window {}")
        (source / "hyprland-greet.conf").write_text("exec-once = regreet")
        with patch("sys.stdin.isatty", return_value=True):
            with self.assertRaises(ValueError):
                LoginSetupService(self.ctx, self.env).apply()
        self.executor.execute.assert_not_called()

    def test_login_passes_immutable_snapshot_to_interactive_helper(self):
        import json
        from dotfiles_api.application.services.login import LoginSetupService

        payload = {'version': 1, 'permissions_only': False, 'user': 'tester',
                   'home': str(self.home), 'files': {}}
        preflight = Mock(root=Path('/'))
        preflight.build.side_effect = lambda **kwargs: dict(payload)
        runner = Mock(return_value=Mock(returncode=0))
        with patch('sys.stdin.isatty', return_value=True):
            backup = LoginSetupService(self.ctx, self.env, preflight=preflight, run=runner,
                                       installer_preflight=Mock()).apply()
        args, options = runner.call_args
        self.assertEqual(args[0][:4], ['sudo', '/usr/bin/python3', '-I', '-c'])
        self.assertEqual(options, {})  # Keep authentication prompts on the terminal.
        self.assertEqual(json.loads(args[0][-1])['home'], str(self.home))
        compile(args[0][-2], '<login-helper>', 'exec')  # Parse only; never run privileged code.
        self.assertTrue(str(backup).startswith('/var/backups/shade-raid/login-'))
        self.executor.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
