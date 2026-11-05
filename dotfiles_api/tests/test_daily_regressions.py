import contextlib
import io
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.actions.browser import BrowserAction
from dotfiles_api.infrastructure.actions.clipboard import ClipboardAction
from dotfiles_api.infrastructure.actions.control import ControlAction
from dotfiles_api.infrastructure.actions.launch import LaunchAction
from types import SimpleNamespace
from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction


class TestDailyRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "events"
        self.env = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                    "TEST_ROOT": str(self.root), "HOME": str(self.root)}
        self.context = ExecutionContext(False, SystemCommandExecutor(), verbose=True, log_path=self.root / "commands.jsonl")

    def command(self, name, code):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + code + "\n")
        path.chmod(0o755)

    def test_running_browser_returns_promptly_and_redacts_url(self):
        self.command("firefox", "sleep 3")
        secret = "https://reset.invalid/path?token=SECRET-CALLBACK#OAUTH"
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as output:
            started = time.monotonic()
            BrowserAction(self.context).execute([secret])
            self.assertLess(time.monotonic() - started, 2)
        self.assertNotIn("SECRET-CALLBACK", output.getvalue() + (self.root / "commands.jsonl").read_text())
        self.assertNotIn("OAUTH", output.getvalue() + (self.root / "commands.jsonl").read_text())

    def test_browser_startup_failure_does_not_expose_url_or_stderr(self):
        self.command("firefox", 'printf "%s\\n" "$*" >&2; exit 4')
        secret = "https://reset.invalid/SECRET-PATH?token=SECRET-TOKEN#SECRET-FRAGMENT"
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(RuntimeError) as error:
                BrowserAction(self.context).execute([secret])
        diagnostics = str(error.exception) + output.getvalue() + (self.root / "commands.jsonl").read_text()
        self.assertNotIn("SECRET", diagnostics)

    def test_cancelled_region_is_read_only(self):
        self.screenshot_tools('exit 0', 'exit 0')
        self.command("slurp", 'exit 1')
        with patch.dict(os.environ, self.env, clear=True):
            ScreenshotAction(self.context).execute(["--region"])
        self.assertFalse((self.root / "Pictures With Spaces").exists())
        self.assertFalse(self.log.exists())

    def screenshot_tools(self, grim, copy):
        self.command("xdg-user-dir", 'printf "%s\\n" "$TEST_ROOT/Pictures With Spaces"')
        self.command("grim", grim)
        self.command("wl-copy", copy)
        self.command("notify-send", 'printf "notify\\n" >> "$TEST_ROOT/events"')

    def test_screenshot_uses_stdin_without_shell_and_path_with_spaces(self):
        self.screenshot_tools('printf image > "$1"', 'cat > "$TEST_ROOT/copied"')
        with patch.dict(os.environ, self.env, clear=True):
            ScreenshotAction(self.context).execute([])
        self.assertEqual((self.root / "copied").read_text(), "image")
        self.assertEqual(self.log.read_text().strip(), "notify")
        self.assertEqual(len(list((self.root / "Pictures With Spaces/Screenshots").glob("*.png"))), 1)

    def test_screenshot_failure_never_calls_copy_or_success_notification(self):
        self.screenshot_tools('exit 42', 'printf copy >> "$TEST_ROOT/events"')
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaises(RuntimeError):
                ScreenshotAction(self.context).execute([])
        self.assertFalse(self.log.exists())
        self.assertEqual(list((self.root / "Pictures With Spaces/Screenshots").glob("*.png")), [])

    def test_clipboard_failure_never_notifies_success(self):
        self.screenshot_tools('printf image > "$1"', 'exit 3')
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaisesRegex(RuntimeError, "clipboard copy failed"):
                ScreenshotAction(self.context).execute([])
        self.assertFalse(self.log.exists())
        self.assertEqual(len(list((self.root / "Pictures With Spaces/Screenshots").glob("*.png"))), 1)

    def test_clipboard_rejects_non_text_before_editor(self):
        self.command("wl-paste", 'printf "image/png\\n"')
        self.command("wl-copy", 'exit 0')
        self.command("ghostty", 'printf invoked > "$TEST_ROOT/events"')
        self.command("nvim", 'exit 0')
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaisesRegex(ValueError, "plain text"):
                ClipboardAction(self.context, env, edit=True).execute([])
        self.assertFalse(self.log.exists())
        self.assertFalse(env.runtime_dir.exists())

    def test_clipboard_text_stays_private_and_is_cleaned_after_editor(self):
        self.command("wl-paste", 'if [ "$1" = "--list-types" ]; then printf "text/plain\\n"; else printf "PRIVATE-CLIPBOARD"; fi')
        self.command("wl-copy", 'cat > "$TEST_ROOT/copied"')
        self.command("ghostty", 'shift; exec "$@"')
        self.command("nvim", 'test "$(stat -c %a "$2")" = 600')
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as output:
            ClipboardAction(self.context, env, edit=True).execute([])
        self.assertEqual((self.root / "copied").read_text(), "PRIVATE-CLIPBOARD")
        self.assertEqual(list(env.runtime_dir.glob("clipboard-*.txt")), [])
        self.assertNotIn("PRIVATE-CLIPBOARD", output.getvalue() + (self.root / "commands.jsonl").read_text())

    def test_osd_installed_but_server_offline_uses_exactly_one_fallback(self):
        self.command("systemctl", 'exit 3')
        self.command("swayosd-client", 'printf "osd\\n" >> "$TEST_ROOT/events"')
        self.command("wpctl", 'printf "wpctl\\n" >> "$TEST_ROOT/events"')
        with patch.dict(os.environ, self.env, clear=True):
            ControlAction(self.context, "volume", "up").execute([])
        self.assertEqual(self.log.read_text().splitlines(), ["wpctl"])

    def test_osd_failure_after_dispatch_does_not_double_apply(self):
        self.command("systemctl", 'exit 0')
        self.command("swayosd-client", 'printf "osd\\n" >> "$TEST_ROOT/events"; exit 1')
        self.command("wpctl", 'printf "wpctl\\n" >> "$TEST_ROOT/events"')
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaises(RuntimeError):
                ControlAction(self.context, "volume", "up").execute([])
        self.assertEqual(self.log.read_text().splitlines(), ["osd"])

    def test_application_launcher_is_nonblocking_and_redacts_arguments(self):
        self.command("mygame", "sleep 2")
        spec = SimpleNamespace(id="game", launch=["mygame"], packages=["mygame"])
        secret = "https://invite.invalid/SECRET-SESSION?token=SECRET"
        processes = []
        spawn = self.context.executor.spawn
        def capture(args, cwd=None):
            process = spawn(args, cwd)
            processes.append(process)
            return process
        with patch.dict(os.environ, self.env, clear=True), patch.object(self.context.executor, "spawn", side_effect=capture):
            start = time.monotonic()
            LaunchAction(self.context, [spec]).execute(["game", secret])
            self.assertLess(time.monotonic() - start, 1.5)
        processes[0].wait(timeout=5)
        self.assertNotIn("SECRET", (self.root / "commands.jsonl").read_text())
