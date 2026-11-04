import tempfile
import unittest
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.application.services.extras import ExtrasSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult


class TestSetupRemediation(unittest.TestCase):
    def test_shell_change_requires_explicit_choice_and_is_idempotent(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / 'repo', 'tester')
            executor = Mock()
            executor.execute.return_value = CommandResult('configured', '', 0)
            service = UserSetupService(ExecutionContext(False, executor), env)
            with patch('pwd.getpwuid', return_value=SimpleNamespace(pw_shell='/usr/bin/fish')):
                service.setup_user(change_shell=True)
            self.assertFalse(any(call.args[0][0] == 'chsh' for call in executor.execute.call_args_list))
            with patch('pwd.getpwuid', return_value=SimpleNamespace(pw_shell='/bin/bash')):
                service.setup_user(change_shell=True)
            self.assertEqual(sum(call.args[0][0] == 'chsh' for call in executor.execute.call_args_list), 1)
    def test_invalid_dotfiles_and_relative_xdg_are_rejected_before_execution(self):
        from dotfiles_api.presentation.cli import main
        cases = ({'DOTFILES_DIR': 'relative-repo'}, {'XDG_STATE_HOME': 'relative-state'})
        for variables in cases:
            with self.subTest(variables=variables), tempfile.TemporaryDirectory() as temp:
                with patch.dict(os.environ, variables, clear=True), patch('pathlib.Path.home', return_value=Path(temp)), \
                        patch('dotfiles_api.infrastructure.executor.SystemCommandExecutor.execute') as executor, \
                        patch('os.geteuid', return_value=1000):
                    with self.assertRaisesRegex(ValueError, 'absolute'):
                        main(['install', '--dry-run'])
                executor.assert_not_called()
                self.assertEqual(list(Path(temp).iterdir()), [])
    def test_setup_preserves_previously_selected_theme(self):
        from dotfiles_api.application.services.setup import SetupService
        from dotfiles_api.application.services.theme import ThemeService
        from dotfiles_api.infrastructure.file_store import FileThemeStore
        from dotfiles_api.domain.events import EventBus
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / 'repo', 'tester')
            store = FileThemeStore(env)
            store.set_active_theme('shade-raid-dark')
            theme = ThemeService(Mock(), store, EventBus())
            service = SetupService(env, ExecutionContext(False, Mock()), Mock(), Mock(), theme,
                                   Mock(), Mock(), Mock(), graphics_package_detector=lambda: [])
            with patch('os.geteuid', return_value=1000), patch('sys.stdin.isatty', return_value=False):
                service.run_setup()
            self.assertEqual(store.get_active_theme(), 'shade-raid-dark')
    def test_direct_setup_rejects_root_before_any_operation(self):
        from dotfiles_api.application.services.setup import SetupService
        executor, installer = Mock(), Mock()
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / 'repo', 'tester')
            service = SetupService(env, ExecutionContext(False, executor), installer,
                                   Mock(), Mock(), Mock(), Mock(), Mock(), graphics_package_detector=lambda: [])
            with patch('os.geteuid', return_value=0), self.assertRaisesRegex(RuntimeError, 'root'):
                service.run_setup()
            installer.install_profile.assert_not_called()
            executor.execute.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])
    def test_bootstrap_dry_run_does_not_plan_unrequested_upgrade_or_firewall(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(['bash', str(root / 'scripts/bootstrap.sh'), '--dry-run'],
                                    env={**os.environ, 'HOME': temp}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('full system upgrade', result.stdout)
            self.assertNotIn('enable multilib', result.stdout)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_installer_preflight_refuses_unknown_launcher_without_writes(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            launcher = home / '.local/bin/dotfiles'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('personal executable')
            result = subprocess.run(['bash', str(root / 'scripts/install-cli.sh'), '--preflight'],
                                    env={**os.environ, 'HOME': temp, 'XDG_DATA_HOME': str(home / '.local/share')},
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(launcher.read_text(), 'personal executable')
            self.assertFalse((home / '.local/share').exists())

    def test_installer_preflight_on_fresh_home_is_read_only(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(['bash', str(root / 'scripts/install-cli.sh'), '--preflight'],
                                    env={**os.environ, 'HOME': temp, 'XDG_DATA_HOME': str(Path(temp) / '.local/share')},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_installer_preflight_rejects_file_in_data_path(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            blocked = home / 'occupied'
            blocked.write_text('personal')
            result = subprocess.run(['bash', str(root / 'scripts/install-cli.sh'), '--preflight'],
                                    env={**os.environ, 'HOME': temp, 'XDG_DATA_HOME': str(blocked / 'nested')},
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(blocked.read_text(), 'personal')
            self.assertFalse((home / '.local').exists())
    def test_setup_does_not_change_firewall_or_shell_or_execute_remote_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / 'repo', 'tester')
            executor = Mock()
            executor.execute.return_value = CommandResult('configured', '', 0)
            execution = ExecutionContext(False, executor)
            ServicesSetupService(execution, env).setup_services(enable_ssh_server=True)
            UserSetupService(execution, env).setup_user()
            commands = [call.args[0] for call in executor.execute.call_args_list]
            self.assertFalse(any('ufw' in cmd or 'chsh' in cmd for cmd in commands))
            self.assertFalse(any('curl' in arg or 'fisher update' in arg for cmd in commands for arg in cmd))

    def test_extras_does_not_execute_remote_marketplace_script(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / 'repo', 'tester')
            executor = Mock()
            executor.execute.return_value = CommandResult('', '', 0)
            service = ExtrasSetupService(ExecutionContext(False, executor), env)
            service._spotify_path = Path(temp) / 'spotify'
            service._spotify_path.mkdir()
            service._prefs_path = Path(temp) / 'prefs'
            service._prefs_path.write_text('prefs')
            with patch('shutil.which', return_value='/usr/bin/tool'):
                service.setup_extras()
            commands = [call.args[0] for call in executor.execute.call_args_list]
            self.assertFalse(any('curl' in arg for cmd in commands for arg in cmd))

    def test_multilib_preflight_uses_effective_pacman_configuration(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            command = Path(temp) / 'pacman-conf'
            command.write_text('#!/bin/sh\nprintf "%s\\n" core extra\n')
            command.chmod(0o755)
            env = {**os.environ, 'PATH': temp + os.pathsep + os.environ['PATH']}
            result = subprocess.run(['bash', str(root / 'scripts/check-desktop-prerequisites.sh')], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('multilib', result.stderr)
            command.write_text('#!/bin/sh\nprintf "%s\\n" core extra multilib\n')
            result = subprocess.run(['bash', str(root / 'scripts/check-desktop-prerequisites.sh')], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
