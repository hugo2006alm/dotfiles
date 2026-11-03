import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.actions.media import MediaAction
from dotfiles_api.infrastructure.actions.control import ControlAction
from dotfiles_api.infrastructure.actions.browser import BrowserAction
from dotfiles_api.tests.test_actions import MockCommandExecutor

ROOT = Path(__file__).resolve().parents[2]


class TestDailyDesktop(unittest.TestCase):
    def test_literal_keybindings_have_no_conflicts(self):
        source = (ROOT / "home/.config/hypr/keybinds.lua").read_text()
        keys = re.findall(r'bind\("([^"]+)",', source)
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("dotfiles action chatgpt", source)
        self.assertIn("dotfiles action launch", source)
        rules = (ROOT / "home/.config/hypr/windowrules.lua").read_text()
        self.assertIn("monitor_w * 0.7", rules)
        self.assertIn("monitor_h * 0.7", rules)

    def test_media_targets_a_playing_player_before_a_paused_player(self):
        executor = MockCommandExecutor()
        executor.mock_results = {"playerctl -l": ("spotify\nfirefox\n", "", 0),
            "playerctl --player spotify status": ("Paused", "", 0),
            "playerctl --player firefox status": ("Playing", "", 0)}
        MediaAction(ExecutionContext(False, executor), "play-pause").execute([])
        self.assertEqual(executor.commands[-1], "playerctl --player firefox play-pause")

    def test_volume_has_exactly_one_mutation_with_or_without_osd(self):
        for installed in (None, "/usr/bin/swayosd-client"):
            executor = MockCommandExecutor()
            with patch("shutil.which", return_value=installed):
                ControlAction(ExecutionContext(False, executor), "volume", "up").execute([])
            self.assertEqual(len(executor.commands), 1)
            self.assertEqual(executor.commands[0].split()[0], "swayosd-client" if installed else "wpctl")

    def test_browser_uses_installed_fallback_and_chatgpt_passes_one_url(self):
        executor = MockCommandExecutor()
        with patch("shutil.which", side_effect=lambda app: "/usr/bin/firefox" if app == "firefox" else None):
            BrowserAction(ExecutionContext(False, executor), chatgpt=True).execute([])
        self.assertEqual(executor.commands, ["firefox https://chatgpt.com/"])

    def test_missing_optional_application_reports_requirement(self):
        from dotfiles_api.infrastructure.actions.launch import LaunchAction
        from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
        executor = MockCommandExecutor()
        with patch("shutil.which", return_value=None), self.assertRaisesRegex(RuntimeError, "steam"):
            LaunchAction(ExecutionContext(False, executor), APPLICATIONS).execute(["gaming"])
        self.assertFalse(any(command.startswith("steam") for command in executor.commands))

    def test_cancelled_screenshot_creates_no_directories(self):
        from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
        with tempfile.TemporaryDirectory() as temp:
            executor = MockCommandExecutor()
            executor.mock_results = {"xdg-user-dir": (temp, "", 0), "slurp": ("", "cancelled", 1)}
            ScreenshotAction(ExecutionContext(False, executor)).execute(["--region"])
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_screenshot_filename_is_passed_as_a_separate_shell_argument(self):
        from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
        executor = Mock()
        with tempfile.TemporaryDirectory(prefix="pictures with spaces ") as temp:
            executor.execute.return_value = CommandResult(temp, "", 0)
            ScreenshotAction(ExecutionContext(False, executor)).execute([])
            commands = [call.args[0] for call in executor.execute.call_args_list]
            copy = next(command for command in commands if command[0] == "sh")
            self.assertEqual(copy[2], 'wl-copy --type image/png < "$1"')
            self.assertTrue(copy[-1].startswith(temp))

    def test_browser_notifications_are_visible_and_ssh_agent_is_not_per_shell(self):
        from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
        from dotfiles_api.application.loader import ThemeLoader
        from dotfiles_api.context.environment import EnvironmentContext
        tokens = ThemeLoader(EnvironmentContext(ROOT, ROOT, "test")).load("shade-raid")
        config = json.loads(next(a.content for a in SwayncGenerator().render(tokens, "shade-raid") if a.artifact_id == "swaync-config"))
        self.assertFalse(config["notification-visibility"])
        fish = (ROOT / "home/.config/fish/config.fish").read_text()
        self.assertNotIn("ssh-agent -c", fish)
        self.assertNotIn("ssh-add -q", fish)
        self.assertTrue((ROOT / "home/.config/systemd/user/shade-raid-ssh-agent.service").is_file())

    def test_clipboard_editor_uses_private_file_and_dry_run_does_not_write(self):
        from dotfiles_api.infrastructure.actions.clipboard import ClipboardAction
        from dotfiles_api.context.environment import EnvironmentContext
        executor = MockCommandExecutor()
        executor.mock_results = {"wl-paste": ("sensitive clipboard text", "", 0)}
        with tempfile.TemporaryDirectory() as temp, patch("shutil.which", return_value="/usr/bin/tool"):
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            with contextlib.redirect_stdout(io.StringIO()):
                ClipboardAction(ExecutionContext(True, executor), env, edit=True).execute([])
            self.assertEqual(list(Path(temp).iterdir()), [])
            ClipboardAction(ExecutionContext(False, executor), env, edit=True).execute([])
            content = next(env.runtime_dir.glob("clipboard-*.txt"))
            self.assertEqual(content.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("sensitive clipboard text", "\n".join(executor.commands))

    def test_recorder_never_signals_an_unrelated_pid(self):
        from dotfiles_api.infrastructure.actions.recorder import RecorderAction
        from dotfiles_api.context.environment import EnvironmentContext
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            executor = MockCommandExecutor()
            action = RecorderAction(ExecutionContext(False, executor), env)
            action._pid_file.parent.mkdir(parents=True)
            action._pid_file.write_text('{"pid": 42, "identity": "old"}')
            with patch.object(action, "_identity", return_value="different"), \
                    patch("subprocess.Popen") as process:
                process.return_value.wait.return_value = 1
                with self.assertRaisesRegex(RuntimeError, "Recorder exited"):
                    action.execute([])
            self.assertFalse(any(command.startswith("kill ") for command in executor.commands))
            self.assertFalse(action._pid_file.exists())

    def test_recorder_stops_its_child_when_pid_state_cannot_be_saved(self):
        import subprocess
        from dotfiles_api.infrastructure.actions.recorder import RecorderAction
        from dotfiles_api.context.environment import EnvironmentContext
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            action = RecorderAction(ExecutionContext(False, MockCommandExecutor()), env)
            with patch("subprocess.Popen") as process, patch.object(action, "_identity", return_value="owned"), \
                    patch("dotfiles_api.infrastructure.actions.recorder.SystemFileWriter.write", side_effect=OSError("disk full")):
                process.return_value.pid = 12345
                process.return_value.wait.side_effect = subprocess.TimeoutExpired("wf-recorder", 0.2)
                with self.assertRaisesRegex(OSError, "disk full"):
                    action.execute([])
                process.return_value.terminate.assert_called_once()

    def test_cli_action_failure_has_visible_feedback_and_still_fails(self):
        from dotfiles_api.presentation.cli import main
        with tempfile.TemporaryDirectory() as temp, patch("pathlib.Path.home", return_value=Path(temp)), \
                patch("dotfiles_api.presentation.cli.ActionService") as actions, \
                patch("dotfiles_api.context.execution.ExecutionContext.optional") as feedback:
            actions.return_value.run_action.side_effect = RuntimeError("capture failed")
            with self.assertRaisesRegex(RuntimeError, "capture failed"):
                main(["action", "record"])
            self.assertIn("Action failed: record", feedback.call_args.args[0])
