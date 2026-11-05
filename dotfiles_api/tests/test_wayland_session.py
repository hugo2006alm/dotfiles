import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.services.wayland_session import WaylandSessionService
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS

ROOT = Path(__file__).resolve().parents[2]
SESSION = {"WAYLAND_DISPLAY": "wayland-1", "XDG_CURRENT_DESKTOP": "Hyprland",
           "XDG_SESSION_TYPE": "wayland", "HYPRLAND_INSTANCE_SIGNATURE": "test-session", "PATH": "/usr/bin"}


class TestWaylandSession(unittest.TestCase):
    def setUp(self):
        self.executor = Mock()
        self.executor.execute.return_value = CommandResult("", "", 0)
        self.service = WaylandSessionService(ExecutionContext(False, self.executor), ApplicationRegistry(APPLICATIONS))

    def commands(self):
        return [call.args[0] for call in self.executor.execute.call_args_list]

    def test_pending_offline_refresh_runs_once_after_session_start(self):
        from dotfiles_api.context.environment import EnvironmentContext
        from dotfiles_api.application.services.reload import ReloadService
        from dotfiles_api.infrastructure.actions.session import SessionAction
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = EnvironmentContext(home, home / 'repo', 'tester')
            pending = env.state_dir / 'pending-refresh'
            pending.parent.mkdir(parents=True)
            pending.write_text('refresh required\n')
            session, wallpaper, handler = Mock(), Mock(), Mock()
            reloads = ReloadService([handler], runtime_dir=env.runtime_dir,
                                    pending_path=pending, output_guard=env.validate_output_path)
            action = SessionAction(session, env, reloads, wallpaper)
            with patch.dict(os.environ, SESSION, clear=True):
                action.execute([])
                action.execute([])
            self.assertEqual(session.start.call_count, 2)
            wallpaper.execute.assert_called_once_with([])
            handler.reload.assert_called_once_with()
            self.assertFalse(pending.exists())

    def test_failed_wallpaper_keeps_pending_refresh_for_retry(self):
        from dotfiles_api.context.environment import EnvironmentContext
        from dotfiles_api.infrastructure.actions.session import SessionAction
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = EnvironmentContext(home, home / 'repo', 'tester')
            pending = env.state_dir / 'pending-refresh'
            pending.parent.mkdir(parents=True)
            pending.write_text('refresh required\n')
            wallpaper, reloads = Mock(), Mock()
            wallpaper.execute.side_effect = RuntimeError('wallpaper failed')
            with self.assertRaisesRegex(RuntimeError, 'wallpaper failed'):
                SessionAction(Mock(), env, reloads, wallpaper).execute([])
            self.assertTrue(pending.exists())
            reloads.reload_all.assert_not_called()

    @unittest.skipUnless(shutil.which('python3'), 'Requires Python')
    def test_walker_waits_for_elephant_socket_and_fails_when_not_ready(self):
        import socket
        import threading
        import time
        script = ROOT / 'home/.local/bin/shade-raid-wait-elephant'
        self.assertTrue(os.access(script, os.X_OK))
        unit = (ROOT / 'home/.config/systemd/user/shade-raid-walker.service').read_text()
        self.assertIn('ExecStartPre=%h/.local/bin/shade-raid-wait-elephant', unit)
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, 'XDG_RUNTIME_DIR': temp}
            missing = subprocess.run(['python3', str(script), '--timeout', '0.1'], env=env,
                                     capture_output=True, text=True, timeout=3)
            self.assertNotEqual(missing.returncode, 0)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            path = Path(temp) / 'elephant/elephant.sock'
            path.parent.mkdir()
            server.bind(str(path))
            def listen_later():
                time.sleep(.1)
                server.listen(1)
                connection, _ = server.accept()
                connection.close()
            thread = threading.Thread(target=listen_later, daemon=True)
            thread.start()
            ready = subprocess.run(['python3', str(script), '--timeout', '2'], env=env,
                                   capture_output=True, text=True, timeout=3)
            thread.join(3)
            server.close()
            self.assertEqual(ready.returncode, 0, ready.stderr)
            self.assertFalse(thread.is_alive())

    def test_environment_import_precedes_idempotent_service_start(self):
        with patch.dict(os.environ, SESSION, clear=True):
            self.service.start()
        commands = self.commands()
        self.assertEqual(commands[0][:3], ["dbus-update-activation-environment", "--systemd", "WAYLAND_DISPLAY"])
        self.assertNotIn("--all", commands[0])
        self.assertIn("PATH", commands[0])
        self.assertEqual(commands[1], ["systemctl", "--user", "daemon-reload"])
        for name in ("waybar", "swaync", "walker", "swayosd", "elephant"):
            self.assertIn(["systemctl", "--user", "start", f"shade-raid-{name}.service"], commands)
        self.assertEqual(commands[-1], ["systemctl", "--user", "start", "xdg-desktop-portal.service"])
        self.assertFalse(any("kill" in arg or "restart" == arg for cmd in commands for arg in cmd))

    def test_environment_import_failure_stops_dependents(self):
        self.executor.execute.return_value = CommandResult("", "bus unavailable", 1)
        with patch.dict(os.environ, SESSION, clear=True), self.assertRaisesRegex(RuntimeError, "bus unavailable"):
            self.service.start()
        self.assertEqual(len(self.commands()), 1)

    def test_missing_wayland_environment_fails_before_starting_anything(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(RuntimeError, "Wayland"):
            self.service.start()
        self.executor.execute.assert_not_called()

    def test_portal_action_uses_the_same_non_disruptive_activation(self):
        from dotfiles_api.infrastructure.actions.portal import PortalAction
        with patch.dict(os.environ, SESSION, clear=True), patch("subprocess.Popen") as process:
            PortalAction(ExecutionContext(False, self.executor)).execute([])
        process.assert_not_called()
        self.assertEqual(self.commands()[-1], ["systemctl", "--user", "start", "xdg-desktop-portal.service"])

    def test_dry_run_does_not_query_or_launch_or_write(self):
        service = WaylandSessionService(ExecutionContext(True, self.executor), ApplicationRegistry(APPLICATIONS))
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True), \
                patch("subprocess.Popen") as process, contextlib.redirect_stdout(io.StringIO()):
            service.start()
            self.assertEqual(list(Path(temp).iterdir()), [])
        self.executor.execute.assert_not_called()
        process.assert_not_called()

    def test_units_follow_session_lifetime_and_autostart_has_one_owner(self):
        source = (ROOT / "home/.config/hypr/autostart.lua").read_text()
        self.assertIn("dotfiles action session", source)
        for spec in APPLICATIONS:
            if not spec.user_unit:
                continue
            content = (ROOT / "home/.config/systemd/user" / spec.user_unit).read_text()
            self.assertIn("PartOf=graphical-session.target", content)
            self.assertIn("BindsTo=hyprland-session.target", content)
            self.assertNotIn('hl.exec_cmd("' + spec.id, source)
        self.assertNotIn("portal.sh", source)
        self.assertFalse((ROOT / "home/.config/hypr/scripts/portal.sh").exists())

    @unittest.skipUnless(shutil.which("systemd-analyze"), "Requires systemd-analyze")
    def test_systemd_verifies_unit_graph_offline_with_stub_application_binaries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            units = root / "config/systemd/user"
            units.mkdir(parents=True)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            stub = root / "application"
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(0o700)
            # Native target fixture follows upstream; applications are never launched.
            (units / "hyprland-session.target").write_text(
                "[Unit]\nDescription=Hyprland session\nBindsTo=graphical-session.target\n"
                "Wants=graphical-session-pre.target\nAfter=graphical-session-pre.target\n"
                "PropagatesStopTo=graphical-session.target\n")
            paths = []
            for source in (ROOT / "home/.config/systemd/user").glob("shade-raid-*.service"):
                content = source.read_text()
                for binary in ("waybar", "swaync", "swayosd-server", "walker", "elephant", "ssh-agent"):
                    content = content.replace(f"/usr/bin/{binary}", str(stub))
                content = content.replace("%h/.local/bin/shade-raid-wait-elephant", str(stub))
                path = units / source.name
                path.write_text(content)
                paths.append(str(path))
            environment = {**os.environ, "XDG_CONFIG_HOME": str(root / "config"), "XDG_RUNTIME_DIR": str(runtime)}
            result = subprocess.run(["systemd-analyze", "--user", "--man=no", "verify", *paths],
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
