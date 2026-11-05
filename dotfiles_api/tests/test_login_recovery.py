import json
import os
import sys
from types import SimpleNamespace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.services.login import LoginSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.login_installation import LoginInstallation
from dotfiles_api.infrastructure.login_preflight import LoginPreflight


class TestLoginRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home/tester'
        self.source = self.home / '.config/greetd'
        self.source.mkdir(parents=True)
        self.files = {'hyprland-greet.conf': 'exec-once = regreet\n',
                      'regreet.toml': '[GTK]\napplication_prefer_dark_theme = true\n',
                      'regreet.css': 'window { background: black; }\n'}
        for name, content in self.files.items():
            (self.source / name).write_text(content)
        self.env = EnvironmentContext(self.home, self.home / 'dotfiles', 'tester')
        self.target = self.root / 'etc/greetd'
        self.target.mkdir(parents=True)
        (self.root / 'etc/sudoers.d').mkdir()
        (self.root / 'etc/systemd/system').mkdir(parents=True)
        (self.root / 'run/lock').mkdir(parents=True)
        (self.root / 'var/backups').mkdir(parents=True)
        self.preflight = LoginPreflight(self.env, root=self.root, which=lambda _: "/usr/bin/true",
                                       greeter_lookup=lambda _: SimpleNamespace(pw_uid=42))

    def install(self, **kwargs):
        kwargs.setdefault('policy_check', lambda: None)
        return LoginInstallation(self.root, owner=os.getuid(), group=os.getgid(), **kwargs)

    def old_state(self):
        (self.target / 'regreet.css').write_text('old css')
        (self.target / 'regreet.css').chmod(0o666)
        (self.target / 'regreet-background.jpg').write_bytes(b'legacy image')
        (self.target / 'regreet-background.jpg').chmod(0o666)
        legacy = self.root / 'etc/sudoers.d/shade-raid'
        legacy.write_text(LoginInstallation.legacy_rule('tester', str(self.home)))
        legacy.chmod(0o440)
        (self.root / 'etc/sudoers.d/regreet-theme').write_text('custom policy')

    def snapshot(self):
        paths = list(self.target.iterdir()) + list((self.root / 'etc/sudoers.d').iterdir())
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mode & 0o777,
                                               p.stat().st_uid, p.stat().st_gid) for p in paths}

    def test_preflight_is_read_only_and_drops_missing_legacy_background(self):
        (self.source / 'regreet.toml').write_text('[background]\npath="/etc/greetd/regreet-background.jpg"\nfit="Cover"\n[GTK]\napplication_prefer_dark_theme=true\n')
        before = sorted(str(p) for p in self.root.rglob('*'))
        payload = self.preflight.build()
        self.assertNotIn('[background]', payload['files']['regreet.toml'])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))
        self.assertIn('config.toml', payload['files'])

    def test_invalid_sources_fail_before_effects(self):
        for name, value in [('regreet.toml', 'invalid = ['), ('hyprland-greet.conf', 'nonsense config'),
                            ('hyprland-greet.conf', 'source = /tmp/unsafe.conf'),
                            ('hyprland-greet.conf', 'exec-once = evil'),
                            ('regreet.css', 'window {'), ('regreet.css', '@import "missing.css";')]:
            with self.subTest(name=name, value=value):
                (self.source / name).write_text(value)
                with self.assertRaises(ValueError):
                    self.preflight.build()
                (self.source / name).write_text(self.files[name])

    def test_missing_binary_and_greeter_fail_preflight(self):
        self.preflight.which = lambda _: None
        with self.assertRaisesRegex(ValueError, 'binary'):
            self.preflight.build()
        self.preflight.which = lambda _: "/usr/bin/true"
        self.preflight.greeter_lookup = Mock(side_effect=KeyError('greeter'))
        with self.assertRaisesRegex(ValueError, 'greeter'):
            self.preflight.build()

    def test_fifo_and_external_symlink_source_are_refused_without_read(self):
        path = self.source / 'regreet.css'
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, 'regular'):
            self.preflight.build()
        path.unlink()
        external = self.root / 'outside.css'
        external.write_text('window {}')
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.preflight.build()

    def test_conflicting_display_manager_blocks_install_but_not_permissions(self):
        dm = self.root / 'etc/systemd/system/display-manager.service'
        dm.symlink_to('/usr/lib/systemd/system/sddm.service')
        with self.assertRaisesRegex(ValueError, 'display manager'):
            self.preflight.build()
        self.old_state()
        result = self.install().apply(self.preflight.build(permissions_only=True))
        self.assertTrue(result.is_dir())
        self.assertEqual(os.readlink(dm), '/usr/lib/systemd/system/sddm.service')

    def test_drift_during_snapshot_is_refused(self):
        original = self.preflight.read_source
        def read(path):
            result = original(path)
            if path.name == 'regreet.css':
                (self.source / 'regreet.toml').write_text('[GTK]\nchanged=true\n')
            return result
        with patch.object(self.preflight, 'read_source', side_effect=read):
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.preflight.build()

    def test_success_installs_root_style_modes_and_preserves_custom_sudoers(self):
        self.old_state()
        before = self.snapshot()
        dm = self.root / 'etc/systemd/system/display-manager.service'
        dm.symlink_to('/usr/lib/systemd/system/greetd.service')
        backup = self.install().apply(self.preflight.build())
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertEqual((backup / 'manifest.json').stat().st_mode & 0o777, 0o600)
        for path in self.target.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)
        self.assertFalse((self.root / 'etc/sudoers.d/shade-raid').exists())
        self.assertEqual((self.root / 'etc/sudoers.d/regreet-theme').read_text(), 'custom policy')
        self.assertEqual(os.readlink(dm), '/usr/lib/systemd/system/greetd.service')
        self.assertEqual((backup / 'greetd/regreet.css').read_bytes(), before['etc/greetd/regreet.css'][0])

    def test_custom_same_name_is_preserved_and_reported(self):
        custom = self.root / 'etc/sudoers.d/shade-raid'
        custom.write_text('tester ALL=(ALL) ALL\n')
        with patch('builtins.print') as output:
            self.install().apply(self.preflight.build())
        self.assertEqual(custom.read_text(), 'tester ALL=(ALL) ALL\n')
        self.assertTrue(any('custom' in str(call).lower() for call in output.call_args_list))

    def test_known_legacy_content_under_unknown_name_is_preserved(self):
        custom = self.root / 'etc/sudoers.d/unrelated'
        custom.write_text(LoginInstallation.legacy_rule('tester', str(self.home)))
        self.install().apply(self.preflight.build())
        self.assertTrue(custom.exists())

    def test_permissions_remediation_needs_no_sources_binaries_or_greeter(self):
        self.old_state()
        for source in self.source.iterdir(): source.unlink()
        self.preflight.which = lambda _: None
        self.preflight.greeter_lookup = Mock(side_effect=KeyError('greeter'))
        before = self.snapshot()
        self.install().apply(self.preflight.build(permissions_only=True))
        self.assertEqual((self.target / 'regreet.css').read_bytes(), before['etc/greetd/regreet.css'][0])
        self.assertEqual((self.target / 'regreet.css').stat().st_mode & 0o777, 0o644)
        self.assertEqual((self.target / 'regreet-background.jpg').stat().st_mode & 0o777, 0o644)
        self.assertFalse((self.target / 'config.toml').exists())

    def test_every_partial_effect_is_compensated_including_interrupt(self):
        self.old_state()
        original = self.snapshot()
        payload = self.preflight.build()
        for fail_at in range(1, 9):
            for exception in (RuntimeError, KeyboardInterrupt):
                with self.subTest(fail_at=fail_at, exception=exception):
                    def fail(step):
                        if step == fail_at: raise exception('injected')
                    with self.assertRaises(exception):
                        self.install(after_effect=fail).apply(payload)
                    self.assertEqual(self.snapshot(), original)
        backups = list((self.root / 'var/backups/shade-raid').iterdir())
        self.assertTrue(all(json.loads((b / 'manifest.json').read_text())['state'] == 'restored' for b in backups))

    def test_permissions_failure_is_compensated(self):
        self.old_state()
        before = self.snapshot()
        def fail(step):
            if step == 2: raise OSError('mode failure')
        with self.assertRaises(OSError):
            self.install(after_effect=fail).apply(self.preflight.build(permissions_only=True))
        self.assertEqual(before, self.snapshot())

    def test_unsafe_destination_types_and_directory_links_have_no_effects(self):
        external = self.root / 'victim'
        external.write_text('private')
        (self.target / 'regreet.css').symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'regular'):
            self.install().apply(self.preflight.build())
        self.assertEqual(external.read_text(), 'private')
        self.assertFalse((self.root / 'var/backups/shade-raid').exists())

    def test_root_rechecks_conflict_after_user_preflight(self):
        payload = self.preflight.build()
        dm = self.root / 'etc/systemd/system/display-manager.service'
        dm.symlink_to('/usr/lib/systemd/system/gdm.service')
        with self.assertRaisesRegex(ValueError, 'display manager'):
            self.install().apply(payload)
        self.assertFalse((self.root / 'var/backups/shade-raid').exists())

    def test_repeated_application_and_permissions_are_safe(self):
        self.old_state()
        self.install().apply(self.preflight.build())
        before = self.snapshot()
        self.install().apply(self.preflight.build())
        self.assertEqual(before, self.snapshot())
        self.install().apply(self.preflight.build(permissions_only=True))
        self.assertEqual(before, self.snapshot())
    def test_target_fifo_is_rejected_and_no_private_backup_is_created(self):
        os.mkfifo(self.target / 'regreet.css')
        with self.assertRaisesRegex(ValueError, 'regular'):
            self.install().apply(self.preflight.build())
        self.assertFalse((self.root / 'var/backups/shade-raid').exists())

    def test_remediation_refuses_unsafe_existing_greetd_command(self):
        (self.target / 'config.toml').write_text('[default_session]\nuser="root"\ncommand="evil"\n')
        with self.assertRaisesRegex(ValueError, 'Unknown greetd session'):
            self.install().apply(self.preflight.build(permissions_only=True))
        self.assertFalse((self.root / 'var/backups/shade-raid').exists())

    def test_invalid_greeter_and_non_executable_binary_are_rejected(self):
        from types import SimpleNamespace
        self.preflight.greeter_lookup = lambda _: SimpleNamespace(pw_uid=0)
        with self.assertRaisesRegex(ValueError, 'greeter'):
            self.preflight.build()
        self.preflight.greeter_lookup = lambda _: SimpleNamespace(pw_uid=42)
        binary = self.root / 'fake-binary'
        binary.write_text('executable missing permission')
        self.preflight.which = lambda _: str(binary)
        with self.assertRaisesRegex(ValueError, 'binary'):
            self.preflight.build()

    def test_semantically_invalid_hypr_values_are_rejected(self):
        (self.source / 'hyprland-greet.conf').write_text('exec-once = regreet\nautogenerated = arbitrary\n')
        with self.assertRaisesRegex(ValueError, 'Hyprland'):
            self.preflight.build()

    def test_dry_run_service_has_no_locks_processes_or_writes(self):
        runner = Mock()
        before = sorted(str(p) for p in self.root.rglob('*'))
        service = LoginSetupService(ExecutionContext(True, Mock()), self.env,
                                   preflight=self.preflight, run=runner,
                                   installer_preflight=self.install().preflight)
        service.apply()
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))
        runner.assert_not_called()

    def test_service_reports_failed_privileged_helper(self):
        runner = Mock(return_value=Mock(returncode=23))
        service = LoginSetupService(ExecutionContext(False, Mock()), self.env,
                                   preflight=self.preflight, run=runner,
                                   installer_preflight=self.install().preflight)
        with patch('sys.stdin.isatty', return_value=True), self.assertRaisesRegex(RuntimeError, '23'):
            service.apply()
        self.assertTrue((self.home / '.shade-raid-locks/login-inputs.lock').is_file())

    def test_input_lock_serializes_other_snapshot_writers(self):
        import threading
        from dotfiles_api.infrastructure.login_lock import login_inputs_lock
        entered, complete = threading.Event(), threading.Event()
        def writer():
            entered.set()
            with login_inputs_lock(self.home):
                complete.set()
        with login_inputs_lock(self.home):
            thread = threading.Thread(target=writer)
            thread.start()
            self.assertTrue(entered.wait(1))
            self.assertFalse(complete.wait(.03))
        thread.join(2)
        self.assertTrue(complete.is_set())

    def test_root_lock_serializes_concurrent_installers(self):
        import threading
        first_inside, release, second_inside = (threading.Event() for _ in range(3))
        errors = []
        def first_effect(step):
            if step == 1:
                first_inside.set()
                if not release.wait(2): raise RuntimeError('test lock timeout')
        def run(installer):
            try: installer.apply(self.preflight.build())
            except BaseException as error: errors.append(error)
        first = threading.Thread(target=run, args=(self.install(after_effect=first_effect),))
        first.start()
        self.assertTrue(first_inside.wait(2))
        second = threading.Thread(target=run, args=(self.install(after_effect=lambda _: second_inside.set()),))
        second.start()
        self.assertFalse(second_inside.wait(.03))
        release.set()
        first.join(5)
        second.join(5)
        self.assertEqual(errors, [])
        self.assertTrue(second_inside.is_set())
    def test_facade_theme_and_setup_join_the_login_input_lock(self):
        from contextlib import contextmanager
        from dotfiles_api.application.facade import DotfilesFacade
        events = []
        @contextmanager
        def tracked(home):
            events.append('locked')
            yield
            events.append('released')
        theme, setup = Mock(), Mock()
        theme.apply_theme.side_effect = lambda _: events.append('theme')
        setup.run_setup.side_effect = lambda _: events.append('setup')
        facade = DotfilesFacade(self.env, ExecutionContext(False, Mock()), Mock(), theme,
                                Mock(), Mock(), setup)
        with patch('dotfiles_api.application.facade.login_inputs_lock', side_effect=tracked):
            facade.apply_theme('shade-raid')
            facade.setup(False)
        self.assertEqual(events, ['locked', 'theme', 'released', 'locked', 'setup', 'released'])
    def test_sudoers_validation_failure_restores_deleted_legacy_rule(self):
        self.old_state()
        before = self.snapshot()
        policy_check = Mock(side_effect=[None, ValueError('invalid policy')])
        with self.assertRaisesRegex(ValueError, 'invalid policy'):
            self.install(policy_check=policy_check).apply(self.preflight.build())
        self.assertEqual(before, self.snapshot())
        self.assertEqual(policy_check.call_count, 2)

    def test_destination_drift_is_rejected_before_overwriting_custom_content(self):
        self.old_state()
        def change(step):
            if step == 1:
                (self.target / 'regreet.css').write_text('custom edit during approval')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.install(after_effect=change).apply(self.preflight.build())
        self.assertEqual((self.target / 'regreet.css').read_text(), 'custom edit during approval')
    def test_failed_recovery_retains_retryable_backup_and_restores_on_retry(self):
        self.old_state()
        before = self.snapshot()
        def fail(step):
            if step == 7: raise RuntimeError('initial failure after sudoers deletion')
        installer = self.install(after_effect=fail)
        write = installer.write
        refused = False
        def write_once(path, *args, **kwargs):
            nonlocal refused
            if path == self.target / 'regreet.css' and args[0] == b'old css' and not refused:
                refused = True
                raise OSError('transient restore error')
            return write(path, *args, **kwargs)
        with patch.object(installer, 'write', side_effect=write_once):
            with self.assertRaisesRegex(RuntimeError, 'recovery incomplete'):
                installer.apply(self.preflight.build())
        backup = next((self.root / 'var/backups/shade-raid').iterdir())
        self.assertEqual(json.loads((backup / 'manifest.json').read_text())['state'], 'recovery-required')
        installer.restore(backup)
        self.assertEqual(before, self.snapshot())
        installer.restore(backup)
        self.assertEqual(before, self.snapshot())

    def test_fresh_install_failure_restores_absent_directory(self):
        self.target.rmdir()
        def fail(step):
            if step == 3: raise KeyboardInterrupt('cancel fresh install')
        with self.assertRaises(KeyboardInterrupt):
            self.install(after_effect=fail).apply(self.preflight.build())
        self.assertFalse(self.target.exists())
    def test_legacy_background_larger_than_config_limit_is_secured(self):
        image = self.target / 'regreet-background.jpg'
        image.write_bytes(b'legacy image' * 10000)
        image.chmod(0o666)
        self.install().apply(self.preflight.build(permissions_only=True))
        self.assertEqual(len(image.read_bytes()), 120000)
        self.assertEqual(image.stat().st_mode & 0o777, 0o644)
