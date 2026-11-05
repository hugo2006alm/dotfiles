import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.services.wayland_session import WaylandSessionService
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS


class TestSSHAgentSelection(unittest.TestCase):
    def test_external_socket_is_verified_and_reused_without_starting_a_second_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            socket_path = str(Path(temp) / 'external.sock')
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(socket_path)
            server.listen(4)
            self.addCleanup(server.close)
            def serve():
                for _ in range(3):
                    connection, _ = server.accept()
                    with connection:
                        self.assertEqual(connection.recv(5), b'\x00\x00\x00\x01\x0b')
                        connection.sendall(b'\x00\x00\x00\x05\x0c\x00\x00\x00\x00')
            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            calls = []
            executor = Mock()
            def execute(args, cwd=None):
                calls.append((args, os.environ.get('SSH_AUTH_SOCK')))
                return CommandResult('', '', 0)
            executor.execute.side_effect = execute
            session = WaylandSessionService(ExecutionContext(False, executor), ApplicationRegistry(APPLICATIONS))
            environment = {'WAYLAND_DISPLAY': 'wayland-1', 'XDG_CURRENT_DESKTOP': 'Hyprland',
                           'XDG_RUNTIME_DIR': temp, 'SSH_AUTH_SOCK': socket_path}
            with patch.dict(os.environ, environment, clear=True):
                for _ in range(3):
                    session.start()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertFalse(any('shade-raid-ssh-agent.service' in args for args, _ in calls))
            self.assertTrue(all(value == socket_path for _, value in calls))

    def test_stale_or_missing_external_socket_uses_managed_path_without_deleting_user_files(self):
        with tempfile.TemporaryDirectory() as temp:
            stale = Path(temp) / 'stale.sock'
            bound = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            bound.bind(str(stale))
            bound.close()
            regular = Path(temp) / 'personal-file'
            regular.write_text('keep')
            managed = str(Path(temp) / 'shade-raid-ssh/agent.socket')
            for previous in ('', str(stale), str(regular), str(Path(temp) / 'missing')):
                with self.subTest(previous=previous):
                    calls = []
                    executor = Mock()
                    executor.execute.side_effect = lambda args, cwd=None: (calls.append((args, os.environ.get('SSH_AUTH_SOCK'))) or CommandResult('', '', 0))
                    session = WaylandSessionService(ExecutionContext(False, executor), ApplicationRegistry(APPLICATIONS))
                    env = {'WAYLAND_DISPLAY': 'wayland-1', 'XDG_CURRENT_DESKTOP': 'Hyprland',
                           'XDG_RUNTIME_DIR': temp, 'SSH_AUTH_SOCK': previous}
                    with patch.dict(os.environ, env, clear=True):
                        session.start()
                    self.assertTrue(any('shade-raid-ssh-agent.service' in args for args, _ in calls))
                    self.assertTrue(all(value == managed for _, value in calls))
            self.assertTrue(stale.is_socket())
            self.assertEqual(regular.read_text(), 'keep')

    def test_connected_non_agent_is_not_trusted(self):
        from dotfiles_api.infrastructure.ssh_agent import agent_responds
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'not-an-agent')
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(path)
            server.listen(1)
            def serve():
                conn, _ = server.accept()
                with conn:
                    conn.recv(5)
                    conn.sendall(b'\x00\x00\x00\x01\x05')
            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            self.assertFalse(agent_responds(path))
            thread.join(2)
            server.close()

    @unittest.skipUnless(__import__('shutil').which('fish'), 'requires fish')
    def test_fish_reuses_external_or_exports_managed_socket_without_spawning_agents(self):
        import subprocess
        root = Path(__file__).resolve().parents[2]
        config = root / 'home/.config/fish/config.fish'
        with tempfile.TemporaryDirectory() as temp:
            helper = Path(temp) / 'ssh-add'
            helper.write_text('#!/bin/sh\nexit "$FAKE_RESULT"\n')
            helper.chmod(0o700)
            for code, expected in [('0', '/external/agent'), ('1', '/external/agent'),
                                   ('2', str(Path(temp) / 'shade-raid-ssh/agent.socket'))]:
                env = {**os.environ, 'HOME': temp, 'XDG_RUNTIME_DIR': temp,
                       'SSH_AUTH_SOCK': '/external/agent', 'FAKE_RESULT': code,
                       'PATH': temp + os.pathsep + os.environ['PATH']}
                for _ in range(3):
                    result = subprocess.run(['fish', '-c', 'source "$argv[1]"; printf "%s" "$SSH_AUTH_SOCK"', str(config)],
                                            env=env, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, expected)

    @unittest.skipUnless(__import__('shutil').which('lua'), 'requires lua')
    def test_hyprland_exports_managed_agent_only_when_external_unavailable(self):
        import subprocess
        root = Path(__file__).resolve().parents[2]
        config = root / 'home/.config/hypr/look_and_feel.lua'
        lua = '''local f=assert(io.open(arg[1])); local src=f:read("*a"); f:close()
local head=assert(src:match("^(.-)%-%- General settings"))
dofile=function() return {} end
hl={env=function(k,v) if k=="SSH_AUTH_SOCK" then print(v) end end}
assert(load(head))()
'''
        with tempfile.TemporaryDirectory() as temp:
            helper = Path(temp) / 'ssh-add'
            helper.write_text('#!/bin/sh\nexit "$FAKE_RESULT"\n')
            helper.chmod(0o700)
            for code, expected in [('0', ''), ('1', ''), ('2', str(Path(temp) / 'shade-raid-ssh/agent.socket') + '\n')]:
                env = {**os.environ, 'HOME': temp, 'XDG_RUNTIME_DIR': temp,
                       'SSH_AUTH_SOCK': '/external/agent', 'FAKE_RESULT': code,
                       'PATH': temp + os.pathsep + os.environ['PATH']}
                result = subprocess.run(['lua', '-', str(config)], input=lua, env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
