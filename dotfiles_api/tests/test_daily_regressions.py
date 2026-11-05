import contextlib
import io
import os
import json
import subprocess
import signal
import sys
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
from dotfiles_api.infrastructure.actions.media import MediaAction
from dotfiles_api.infrastructure.actions.launch import LaunchAction
from types import SimpleNamespace
from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
from dotfiles_api.infrastructure.actions.recorder import RecorderAction


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
        processes = []
        spawn = self.context.executor.spawn
        def capture(args, cwd=None):
            process = spawn(args, cwd)
            processes.append(process)
            return process
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as output, \
                patch.object(self.context.executor, "spawn", side_effect=capture):
            started = time.monotonic()
            BrowserAction(self.context).execute([secret])
            self.assertLess(time.monotonic() - started, 5)
        processes[0].wait(timeout=5)
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
        self.command("nvim", 'for path do :; done; test "$(stat -Lc %a "$path")" = 600 && printf EDITED-TEXT > "$path"')
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as output:
            ClipboardAction(self.context, env, edit=True).execute([])
        self.assertEqual((self.root / "copied").read_text(), "EDITED-TEXT")
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

    def test_media_handles_player_disappearing_and_selects_playing_player(self):
        self.command("playerctl", 'if [ "$1" = -l ]; then printf "gone\\npaused\\nplaying\\n"; elif [ "$3" = status ]; then case "$2" in gone) exit 2;; paused) echo Paused;; playing) echo Playing;; esac; else printf "%s\\n" "$*" >> "$TEST_ROOT/events"; fi')
        with patch.dict(os.environ, self.env, clear=True):
            MediaAction(self.context, "pause").execute([])
        self.assertEqual(self.log.read_text().strip(), "--player playing pause")

    def test_media_absent_or_error_is_nonfatal(self):
        self.command("playerctl", 'exit 2')
        self.command("notify-send", 'exit 0')
        with patch.dict(os.environ, self.env, clear=True):
            MediaAction(self.context, "pause").execute([])
        self.assertFalse(self.log.exists())

    def test_real_recorder_stop_waits_for_finalization(self):
        executable = self.bin / "wf-recorder"
        executable.write_text("""#!/usr/bin/python3
import ctypes, signal, sys, time
ctypes.CDLL(None).prctl(15, b'wf-recorder', 0, 0, 0)
path = sys.argv[2]
def stop(*_):
    with open(path, 'ab') as out: out.write(b'TRAILER')
    sys.exit(0)
signal.signal(signal.SIGINT, stop)
with open(path, 'wb') as out: out.write(b'HEADER')
while True: time.sleep(.05)
""")
        executable.chmod(0o755)
        self.command("xdg-user-dir", 'printf "%s\\n" "$TEST_ROOT/Videos"')
        self.command("notify-send", 'exit 0')
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        action = RecorderAction(self.context, env)
        with patch.dict(os.environ, self.env, clear=True):
            action.execute([])
            record = json.loads(action._pid_file.read_text())
            try:
                action.execute([])
            finally:
                try: os.waitpid(record["pid"], 0)
                except ChildProcessError: pass
        self.assertEqual(Path(record["output"]).read_bytes(), b"HEADERTRAILER")
        self.assertFalse(action._pid_file.exists())

    def test_recorder_pid_change_between_open_and_signal_never_signals_other_process(self):
        process = subprocess.Popen(["sleep", "30"])
        self.addCleanup(lambda: process.poll() is None and process.terminate())
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        action = RecorderAction(self.context, env)
        action._pid_file.parent.mkdir(parents=True)
        action._pid_file.write_text(json.dumps({"pid": process.pid, "identity": "expected", "output": "irrelevant"}))
        with patch.object(action, "_identity", side_effect=["expected", "different"]):
            with self.assertRaisesRegex(RuntimeError, "changed before stop"):
                action.execute([])
        self.assertIsNone(process.poll())
        process.terminate()
        process.wait(timeout=2)

    def test_clipboard_buffer_disappears_after_parent_sigkill(self):
        self.command("wl-paste", 'if [ "$1" = "--list-types" ]; then echo text/plain; else printf KILL-SECRET; fi')
        self.command("wl-copy", 'exit 0')
        self.command("nvim", 'exit 0')
        self.command("ghostty", 'for path do :; done; printf "%s" "$path" > "$TEST_ROOT/events"; sleep 30')
        source = (
            'from pathlib import Path; from dotfiles_api.context.environment import EnvironmentContext; '
            'from dotfiles_api.context.execution import ExecutionContext; from dotfiles_api.infrastructure.executor import SystemCommandExecutor; '
            'from dotfiles_api.infrastructure.actions.clipboard import ClipboardAction; '
            f'ClipboardAction(ExecutionContext(False, SystemCommandExecutor()), EnvironmentContext(Path({str(self.root)!r}), Path({str(self.root / "repo")!r}), "test"), edit=True).execute([])'
        )
        proc = subprocess.Popen([sys.executable, "-c", source], env={**self.env, "PYTHONPATH": os.getcwd()}, start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            while not self.log.exists() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(.05)
            self.assertTrue(self.log.exists(), "editor did not start")
            buffer_path = Path(self.log.read_text())
            self.assertEqual(buffer_path.read_bytes(), b"KILL-SECRET")
            os.kill(proc.pid, signal.SIGKILL)
            proc.wait(timeout=3)
            self.assertFalse(buffer_path.exists())
            self.assertFalse((self.root / ".local").exists())
        finally:
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            if proc.poll() is None: proc.wait(timeout=3)

    def test_screenshot_names_are_unique(self):
        self.screenshot_tools('printf image > "$1"', 'cat > /dev/null')
        with patch.dict(os.environ, self.env, clear=True):
            ScreenshotAction(self.context).execute([])
            ScreenshotAction(self.context).execute([])
        self.assertEqual(len(list((self.root / "Pictures With Spaces/Screenshots").glob("*.png"))), 2)

    def test_recorder_readiness_requires_real_output(self):
        env = EnvironmentContext(self.root, self.root / "repo", "test")
        action = RecorderAction(self.context, env)
        proc = subprocess.Popen(["sleep", "3"])
        try:
            with self.assertRaisesRegex(RuntimeError, "did not produce output"):
                action._wait_ready(proc, self.root / "absent.mkv", timeout=.1)
        finally:
            proc.terminate()
            proc.wait(timeout=2)
