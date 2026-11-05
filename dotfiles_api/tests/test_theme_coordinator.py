import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.tests.test_dry_run_safety import snapshot


class TestThemeCoordinator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.env = EnvironmentContext(root / "user", root / "repo", "tester")
        self.env.home_dir.mkdir()
        self.first = self.env.home_dir / ".config/first.conf"
        self.first.parent.mkdir()
        self.first.write_text("original")
        self.first.chmod(0o640)
        os.utime(self.first, ns=(1_700_000_000_000_000_000,) * 2)
        self.second = self.env.home_dir / ".config/new/second.conf"
        self.store = ArtifactStore({"first": self.first, "second": self.second,
                                    "theme-preview": self.env.preview_file,
                                    "active-theme": self.env.state_dir / "active-theme"})
        self.writer = SystemFileWriter()
        self.transaction = ConfigTransaction(self.env, self.store, self.writer)
        self.generator = Mock()
        self.generator.name = "example"
        self.generator.transaction = self.transaction
        self.generator.render.return_value = [GeneratedArtifact("first", "changed"),
                                              GeneratedArtifact("second", "new")]
        self.planner = ThemePlanner(self.env, self.store, [self.generator])

    def coordinator(self):
        self.assertIsNotNone(importlib.util.find_spec("dotfiles_api.application.theme_coordinator"),
                             "Theme application needs one coordinator")
        from dotfiles_api.application.theme_coordinator import ThemeCoordinator
        return ThemeCoordinator(self.env, self.planner, self.transaction)

    def apply(self, coordinator, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return coordinator.apply(Mock(), "shade-raid-dark", **kwargs)

    def test_offline_refresh_is_persisted_and_retried_in_session(self):
        from dotfiles_api.application.services.reload import ReloadService
        from dotfiles_api.domain.contracts.reloadable import EventReloadable
        class Handler(EventReloadable):
            def __init__(self):
                self.count = 0
            def supports(self, name):
                return name == 'example'
            def reload(self):
                self.count += 1
        handler = Handler()
        pending = self.env.state_dir / 'pending-refresh'
        reloads = ReloadService([handler], runtime_dir=self.env.runtime_dir,
                                pending_path=pending, output_guard=self.env.validate_output_path)
        with patch.dict(os.environ, {}, clear=True):
            reloads.reload_changed({'example'})
        self.assertEqual(handler.count, 0)
        self.assertTrue(pending.is_file())
        self.assertEqual(pending.stat().st_mode & 0o777, 0o600)
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-test'}, clear=True):
            reloads.reload_all()
        self.assertEqual(handler.count, 1)
        self.assertFalse(pending.exists())

    def test_all_generation_finishes_before_any_write_or_active_state_change(self):
        broken = Mock()
        broken.transaction = self.transaction
        broken.render.side_effect = ValueError("render failed")
        self.planner.generators.append(broken)
        coordinator = self.coordinator()
        before = snapshot(self.env.home_dir)
        with self.assertRaisesRegex(ValueError, "render failed"):
            self.apply(coordinator)
        self.assertEqual(snapshot(self.env.home_dir), before)

    def test_invalid_generated_json_fails_before_writing_any_artifact(self):
        self.store = ArtifactStore({"first": self.first, "second": self.second.with_suffix(".json"),
                                    "theme-preview": self.env.preview_file,
                                    "active-theme": self.env.state_dir / "active-theme"})
        self.planner.store = self.store
        self.transaction._store = self.store
        self.generator.render.return_value = [GeneratedArtifact("first", "changed"),
                                              GeneratedArtifact("second", "{broken")]
        coordinator = self.coordinator()
        before = snapshot(self.env.home_dir)
        with self.assertRaises(ValueError):
            self.apply(coordinator)
        self.assertEqual(snapshot(self.env.home_dir), before)

    def test_write_failure_restores_old_metadata_and_removes_new_outputs(self):
        coordinator = self.coordinator()
        original_stat = self.first.stat()
        write = self.writer.write
        def fail_second(path, content):
            if path == self.second:
                raise OSError("injected write failure")
            write(path, content)
        with patch.object(self.writer, "write", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "injected"):
                self.apply(coordinator)
        self.assertEqual(self.first.read_text(), "original")
        self.assertEqual(self.first.stat().st_mode, original_stat.st_mode)
        self.assertEqual(self.first.stat().st_mtime_ns, original_stat.st_mtime_ns)
        self.assertFalse(self.second.exists())
        self.assertFalse(self.second.parent.exists())
        self.assertFalse((self.env.state_dir / "active-theme").exists())
        journals = list((self.env.state_dir / "transactions").glob("*/manifest.json"))
        self.assertEqual(json.loads(journals[0].read_text())["status"], "rolled_back")

    def test_recovery_preserves_non_utf8_original_bytes(self):
        original = b"\xff\x00old config"
        self.first.write_bytes(original)
        coordinator = self.coordinator()
        write = self.writer.write
        def fail(path, content):
            if path == self.second:
                raise OSError("injected")
            write(path, content)
        with patch.object(self.writer, "write", side_effect=fail):
            with self.assertRaisesRegex(OSError, "injected"):
                self.apply(coordinator)
        self.assertEqual(self.first.read_bytes(), original)

    def test_interrupt_during_application_also_recovers_files(self):
        coordinator = self.coordinator()
        write = self.writer.write
        def interrupt(path, content):
            if path == self.second:
                raise KeyboardInterrupt()
            write(path, content)
        with patch.object(self.writer, "write", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.apply(coordinator)
        self.assertEqual(self.first.read_text(), "original")
        self.assertFalse(self.second.exists())
        self.assertFalse((self.env.state_dir / "active-theme").exists())

    def test_success_can_be_rolled_back_including_absent_active_state(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        self.assertEqual(self.first.read_text(), "changed")
        self.assertEqual(self.second.read_text(), "new")
        self.assertEqual(FileThemeStore(self.env).get_active_theme(), "shade-raid-dark")
        personal = self.env.home_dir / "personal.txt"
        personal.write_text("keep")
        with contextlib.redirect_stdout(io.StringIO()):
            coordinator.rollback()
        self.assertEqual(self.first.read_text(), "original")
        self.assertFalse(self.second.exists())
        self.assertFalse((self.env.state_dir / "active-theme").exists())
        self.assertEqual(personal.read_text(), "keep")

    def test_repeated_theme_keeps_unchanged_files_and_creates_no_extra_journal(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        before = self.first.stat().st_mtime_ns
        journals = list((self.env.state_dir / "transactions").iterdir())
        plan = self.apply(coordinator)
        self.assertFalse(plan.changed_generators)
        self.assertEqual(self.first.stat().st_mtime_ns, before)
        self.assertEqual(list((self.env.state_dir / "transactions").iterdir()), journals)

    def test_edit_between_planning_and_application_is_preserved(self):
        coordinator = self.coordinator()
        plan = self.planner.build(Mock(), "shade-raid-dark")
        self.first.write_text("external edit")
        with patch.object(self.planner, "build", return_value=plan):
            with self.assertRaisesRegex(RuntimeError, "changed"):
                self.apply(coordinator)
        self.assertEqual(self.first.read_text(), "external edit")
        self.assertFalse(self.second.exists())

    def test_failed_partial_rollback_can_be_retried_without_overwriting_edits(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        restore = SystemFileWriter.write_bytes
        def fail_first(writer, path, content):
            if path == self.first and content == b"original":
                raise OSError("injected restore failure")
            return restore(writer, path, content)
        with patch.object(SystemFileWriter, "write_bytes", fail_first):
            with self.assertRaisesRegex(RuntimeError, "injected restore failure"):
                coordinator.rollback()
        self.assertFalse(self.second.exists())
        self.assertEqual(self.first.read_text(), "changed")
        journal = next((self.env.state_dir / "transactions").glob("*/manifest.json"))
        manifest = json.loads(journal.read_text())
        self.assertEqual(manifest["status"], "rolling_back")
        states = {record["artifact_id"]: record.get("recovery") for record in manifest["files"]}
        self.assertEqual(states["first"], "restoring")
        self.assertEqual(states["second"], "restored")
        coordinator.rollback()
        self.assertEqual(self.first.read_text(), "original")
        self.assertFalse(self.second.exists())

    def test_legacy_journal_is_recoverable_and_future_version_is_rejected(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        journal = next((self.env.state_dir / 'transactions').glob('*/manifest.json'))
        manifest = json.loads(journal.read_text())
        self.assertEqual(manifest['version'], 1)
        manifest['version'] = 99
        journal.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'version'):
            coordinator.rollback()
        self.assertEqual(self.first.read_text(), 'changed')
        manifest.pop('version')
        journal.write_text(json.dumps(manifest))
        coordinator.rollback()
        self.assertEqual(self.first.read_text(), 'original')

    def test_manual_rollback_dry_run_is_read_only(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        before = snapshot(self.env.home_dir)
        with contextlib.redirect_stdout(io.StringIO()):
            coordinator.rollback(dry_run=True)
        self.assertEqual(snapshot(self.env.home_dir), before)

    def test_manual_rollback_refuses_to_overwrite_newer_personal_edits(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        self.first.write_text("personal edit")
        with self.assertRaisesRegex(RuntimeError, "changed"):
            coordinator.rollback()
        self.assertEqual(self.first.read_text(), "personal edit")
        self.assertEqual(FileThemeStore(self.env).get_active_theme(), "shade-raid-dark")

    def test_rollback_remains_available_when_runtime_directory_changes(self):
        coordinator = self.coordinator()
        self.apply(coordinator)
        new_env = EnvironmentContext(self.env.home_dir, self.env.dotfiles_dir, "tester",
                                     runtime_home=self.env.home_dir / "new-runtime")
        mappings = {"first": self.first, "second": self.second,
                    "active-theme": new_env.state_dir / "active-theme",
                    "theme-preview": new_env.preview_file}
        from dotfiles_api.application.theme_coordinator import ThemeCoordinator
        transaction = ConfigTransaction(new_env, ArtifactStore(mappings), self.writer)
        with contextlib.redirect_stdout(io.StringIO()):
            ThemeCoordinator(new_env, self.planner, transaction).rollback()
        self.assertEqual(self.first.read_text(), "original")
        self.assertFalse(self.second.exists())

    def test_prepared_journal_recovers_a_mix_of_original_links_and_new_files(self):
        external = self.env.home_dir / "external"
        external.write_text("personal")
        self.first.unlink()
        self.first.symlink_to(external)
        coordinator = self.coordinator()
        self.apply(coordinator)
        journal = next((self.env.state_dir / "transactions").glob("*/manifest.json"))
        manifest = json.loads(journal.read_text())
        manifest["status"] = "prepared"
        journal.write_text(json.dumps(manifest))
        self.first.unlink()
        self.first.symlink_to(external)
        with contextlib.redirect_stdout(io.StringIO()):
            coordinator.rollback()
        self.assertTrue(self.first.is_symlink())
        self.assertEqual(external.read_text(), "personal")
        self.assertFalse(self.second.exists())

    def test_incomplete_recovery_is_reported_and_backup_retained(self):
        coordinator = self.coordinator()
        write = self.writer.write
        restore = SystemFileWriter.write_bytes
        def fail_application(path, content):
            if path == self.second:
                raise OSError("apply failed")
            write(path, content)
        def fail_recovery(writer, path, content):
            if path == self.first and content == b"original":
                raise OSError("restore failed")
            restore(writer, path, content)
        with patch.object(self.writer, "write", side_effect=fail_application), \
                patch.object(SystemFileWriter, "write_bytes", fail_recovery):
            with self.assertRaisesRegex(RuntimeError, "recovery incomplete"):
                self.apply(coordinator)
        journal = next((self.env.state_dir / "transactions").glob("*/manifest.json"))
        self.assertEqual((journal.parent / "backups/0").read_bytes(), b"original")

    def test_atomic_writer_replaces_symlink_without_overwriting_its_target(self):
        external = self.env.home_dir / "external.conf"
        external.write_text("personal")
        link = self.env.home_dir / "generated.conf"
        link.symlink_to(external)
        self.writer.write(link, "generated")
        self.assertEqual(external.read_text(), "personal")
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(), "generated")
