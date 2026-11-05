import contextlib
import io
import json
import re
import os
import shutil
import subprocess
import tempfile
import unittest
import shutil
import subprocess
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

    @unittest.skipUnless(shutil.which('lua'), 'Requires Lua')
    def test_expanded_keybind_loops_are_unique_and_actions_exist(self):
        from dotfiles_api.application.services.action import ActionService
        from dotfiles_api.presentation.cli import main
        script = r'''
local function stub() return 'dispatcher' end
hl = {
  dsp = { exec_cmd = function(cmd) return cmd end,
          window = {close=stub, fullscreen=stub, move=stub, resize=stub, float=stub, pseudo=stub, drag=stub},
          exit=stub, focus=stub },
  bind = function(key, action) print(key .. '\t' .. tostring(action)) end
}
dofile(arg[1])
'''
        result = subprocess.run(['lua', '-', str(ROOT / 'home/.config/hypr/keybinds.lua')],
                                input=script, capture_output=True, text=True, timeout=10, check=True)
        bindings = [line.split('\t', 1) for line in result.stdout.splitlines()]
        keys = [key for key, _ in bindings]
        self.assertEqual(len(keys), len(set(keys)), 'expanded keybinds must not conflict')
        for key in ('SUPER + 1', 'SUPER + SHIFT + 0', 'SUPER + KP_End', 'SUPER + SHIFT + KP_Insert'):
            self.assertIn(key, keys)
        registered = set()
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'DOTFILES_DIR': str(ROOT)}, clear=True), \
                patch('pathlib.Path.home', return_value=Path(temp)), \
                patch.object(ActionService, 'register', autospec=True, side_effect=lambda _, name, action: registered.add(name)), \
                patch.object(ActionService, 'run_action'):
            main(['--dry-run', 'action', 'screenshot'])
        from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
        launchable = {spec.id for spec in APPLICATIONS if spec.launch}
        for key, command in bindings:
            launch = re.match(r"dotfiles action launch ([a-z0-9-]+)", command)
            if launch:
                self.assertIn(launch.group(1), launchable, f"{key} refers to unavailable launcher")
            match = re.match(r'dotfiles action ([a-z0-9-]+)', command)
            if match:
                self.assertIn(match.group(1), registered, f'{key} refers to unregistered action')

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
            mutations = [command for command in executor.commands if not command.startswith("systemctl ")]
            self.assertEqual(len(mutations), 1)
            self.assertEqual(mutations[0].split()[0], "swayosd-client" if installed else "wpctl")

    def test_browser_uses_installed_fallback_and_chatgpt_passes_one_url(self):
        execution = Mock(dry_run=False)
        with patch("shutil.which", side_effect=lambda app: "/usr/bin/firefox" if app == "firefox" else None):
            BrowserAction(execution, chatgpt=True).execute([])
        execution.spawn.assert_called_once_with(["firefox", "https://chatgpt.com/"], step="launch:browser", sensitive=True)

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
        executor.mock_results = {"wl-paste --list-types": ("text/plain", "", 0), "wl-paste --type": ("sensitive clipboard text", "", 0)}
        with tempfile.TemporaryDirectory() as temp, patch("shutil.which", return_value="/usr/bin/tool"):
            env = EnvironmentContext(Path(temp), ROOT, "tester")
            with contextlib.redirect_stdout(io.StringIO()):
                ClipboardAction(ExecutionContext(True, executor), env, edit=True).execute([])
            self.assertEqual(list(Path(temp).iterdir()), [])
            ClipboardAction(ExecutionContext(False, executor), env, edit=True).execute([])
            self.assertFalse(env.runtime_dir.exists())
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
                with self.assertRaisesRegex(RuntimeError, "Previous recorder is no longer active"):
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
            with patch("subprocess.Popen") as process, patch.object(action, "_identity", return_value="owned"), patch.object(action, "_wait_ready"), \
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

    @unittest.skipUnless(shutil.which("lua"), "Requires Lua interpreter")
    def test_empty_ssh_environment_exports_the_shared_socket(self):
        source = ROOT / "home/.config/hypr/autostart.lua"
        script = f'''local captured = nil
os.getenv = function(name)
    if name == "XDG_RUNTIME_DIR" then return "/run/user/1000" end
    return ""
end
hl = {{ env = function(key, value) captured = value end, on = function() end }}
assert(loadfile({json.dumps(str(source))}))()
assert(captured == "/run/user/1000/shade-raid-ssh/agent.socket", "shared agent socket was not exported")
'''
        result = subprocess.run(["lua", "-"], input=script, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
