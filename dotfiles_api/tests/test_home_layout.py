import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.linker import StowLinker

ROOT = Path(__file__).resolve().parents[2]


class TestHomeLayout(unittest.TestCase):
    def test_declarative_package_excludes_generated_and_internal_files(self):
        package = ROOT / "home"
        self.assertTrue(package.is_dir(), "Stow needs a dedicated home/ package")
        self.assertTrue((package / ".config/hypr/hyprland.lua").is_file())
        self.assertFalse((package / ".config/swaync/config.json").exists())
        self.assertFalse((package / ".config/greetd/regreet.css").exists())
        self.assertFalse((package / "dotfiles_api").exists())

    def test_dry_run_rejects_missing_home_package_without_writing(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            root.mkdir()
            home.mkdir()
            executor = Mock()
            with self.assertRaisesRegex(ValueError, "package"):
                StowLinker(ExecutionContext(True, executor)).link(root, home)
            executor.execute.assert_not_called()
            self.assertEqual(list(home.iterdir()), [])

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_stow_links_files_without_folding_or_installing_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            source = root / "home/.config/example"
            source.mkdir(parents=True)
            (source / "static.conf").write_text("static")
            (root / "AGENTS.md").write_text("internal")
            (root / "dotfiles_api").mkdir()
            linker = StowLinker(ExecutionContext(False, SystemCommandExecutor()))
            linker.link(root, home)
            self.assertFalse((home / ".config").is_symlink())
            self.assertFalse((home / ".config/example").is_symlink())
            self.assertTrue((home / ".config/example/static.conf").is_symlink())
            self.assertFalse((home / "AGENTS.md").exists())
            self.assertFalse((home / "dotfiles_api").exists())
            generated = home / ".config/example/generated.conf"
            generated.write_text("runtime")
            linker.link(root, home)
            self.assertEqual(generated.read_text(), "runtime")
            self.assertFalse((source / "generated.conf").exists())

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_legacy_fold_is_unfolded_and_personal_files_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            root.mkdir()
            home.mkdir()
            old = root / ".config/example"
            old.mkdir(parents=True)
            (old / "static.conf").write_text("new static")
            (old / "personal.conf").write_text("personal data")
            source = root / "home/.config/example"
            source.mkdir(parents=True)
            (source / "static.conf").write_text("new static")
            (home / ".config").symlink_to(root / ".config")
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            self.assertFalse((home / ".config").is_symlink())
            self.assertEqual((home / ".config/example/static.conf").read_text(), "new static")
            self.assertEqual((home / ".config/example/personal.conf").read_text(), "personal data")
            self.assertEqual((old / "personal.conf").read_text(), "personal data")
            backups = list(home.glob(".shade-raid-backups/stow-*/manifest.json"))
            self.assertEqual(len(backups), 1)

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_conflict_restores_folded_links_without_changing_personal_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            source = root / "home/.config/example"
            source.mkdir(parents=True)
            (source / "static.conf").write_text("static")
            old = root / ".local/bin"
            old.mkdir(parents=True)
            (old / "old-command").write_text("personal command")
            (root / "home/.local/bin").mkdir(parents=True)
            (root / "home/.local/bin/command").write_text("new command")
            (home / ".local").symlink_to(root / ".local")
            target = home / ".config/example"
            target.mkdir(parents=True)
            (target / "static.conf").write_text("personal conflict")
            with self.assertRaises(RuntimeError):
                StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            self.assertTrue((home / ".local").is_symlink())
            self.assertEqual((target / "static.conf").read_text(), "personal conflict")
            self.assertEqual((old / "old-command").read_text(), "personal command")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_legacy_conflicting_overlap_preserved_before_unfolding(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            old = root / ".config/example"
            old.mkdir(parents=True)
            (old / "value").write_text("personal")
            new = root / "home/.config/example"
            new.mkdir(parents=True)
            (new / "value").write_text("default")
            (home / ".config").symlink_to(root / ".config")
            with self.assertRaisesRegex(ValueError, "conflicts"):
                StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            self.assertTrue((home / ".config").is_symlink())
            self.assertEqual((home / ".config/example/value").read_text(), "personal")
            self.assertFalse((home / ".shade-raid-backups").exists())

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_unfold_preserves_private_modes_and_relative_link_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            old = root / ".config/private"
            old.mkdir(parents=True)
            (root / ".config").chmod(0o700)
            old.chmod(0o700)
            external = root / "outside"
            external.write_text("secret")
            (old / "link").symlink_to("../../outside")
            (root / "home/.config/private").mkdir(parents=True)
            (home / ".config").symlink_to(root / ".config")
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            self.assertEqual((home / ".config").stat().st_mode & 0o777, 0o700)
            self.assertEqual((home / ".config/private").stat().st_mode & 0o777, 0o700)
            self.assertEqual((home / ".config/private/link").resolve(), external)
            self.assertEqual((home / ".config/private/link").read_text(), "secret")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_seeds_are_personal_files_and_never_replace_existing_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            (root / "home/.config/app").mkdir(parents=True)
            seed = root / "seeds/.config/app/preferences"
            seed.parent.mkdir(parents=True)
            seed.write_text("default")
            linker = StowLinker(ExecutionContext(False, SystemCommandExecutor()))
            linker.link(root, home)
            installed = home / ".config/app/preferences"
            self.assertFalse(installed.is_symlink())
            installed.write_text("personal")
            linker.link(root, home)
            self.assertEqual(installed.read_text(), "personal")
            self.assertEqual(seed.read_text(), "default")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_existing_mutable_repo_link_becomes_independent_personal_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            (home / ".config").mkdir(parents=True)
            (root / "home/.config").mkdir(parents=True)
            old = root / ".config/mimeapps.list"
            old.parent.mkdir(parents=True)
            old.write_text("personal")
            seed = root / "seeds/.config/mimeapps.list"
            seed.parent.mkdir(parents=True)
            seed.write_text("default")
            (home / ".config/mimeapps.list").symlink_to(old)
            StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            installed = home / ".config/mimeapps.list"
            self.assertFalse(installed.is_symlink())
            self.assertEqual(installed.read_text(), "personal")
            installed.write_text("new personal")
            self.assertEqual(old.read_text(), "personal")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow integration requires stow")
    def test_interrupted_seed_copy_leaves_no_partial_personal_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            (root / "home/.config").mkdir(parents=True)
            seed = root / "seeds/.config/preferences"
            seed.parent.mkdir(parents=True)
            seed.write_text("default")
            def fail(source, out):
                out.write(b"partial")
                raise OSError("disk full")
            with patch("dotfiles_api.infrastructure.linker.shutil.copyfileobj", fail):
                with self.assertRaisesRegex(OSError, "disk full"):
                    StowLinker(ExecutionContext(False, SystemCommandExecutor())).link(root, home)
            self.assertFalse((home / ".config/preferences").exists())
            self.assertEqual(list((home / ".config").glob(".shade-raid-seed-*")), [])

    def test_failure_retains_data_written_during_unfolding(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            home.mkdir()
            (root / ".local").mkdir(parents=True)
            (root / ".local/old").write_text("old")
            (root / "home/.local").mkdir(parents=True)
            (home / ".local").symlink_to(root / ".local")
            class FailAfterWrite:
                dry_run = False
                def execute(self, *args, **kwargs):
                    (home / ".local/new-data").write_text("must survive")
                    raise RuntimeError("stow failed")
            with self.assertRaisesRegex(RuntimeError, "stow failed"):
                StowLinker(FailAfterWrite()).link(root, home)
            self.assertTrue((home / ".local").is_symlink())
            saved = list(home.glob(".shade-raid-backups/stow-*/failed-contents/.local/new-data"))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].read_text(), "must survive")

    def test_theme_output_paths_never_target_repository(self):
        source = (ROOT / "dotfiles_api/presentation/cli.py").read_text()
        self.assertFalse('env.dotfiles_dir / "plymouth-shade-raid"' in source,
                         "Plymouth output must live outside the repository")

    def test_command_logs_cannot_write_through_legacy_local_fold(self):
        from unittest.mock import Mock
        from dotfiles_api.context.environment import EnvironmentContext
        self.assertIn("output_guard", ExecutionContext.__dataclass_fields__)
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            (root / ".local").mkdir(parents=True)
            home.mkdir()
            (home / ".local").symlink_to(root / ".local")
            env = EnvironmentContext(home, root, "tester")
            executor = Mock()
            from dotfiles_api.domain.contracts import CommandResult
            executor.execute.return_value = CommandResult("", "", 0)
            context = ExecutionContext(False, executor, log_path=env.state_dir / "commands.jsonl",
                                       output_guard=env.validate_output_path)
            context.execute(["notify-send", "example"])
            executor.execute.assert_called_once()
            self.assertFalse((root / ".local/state").exists())

    def test_failed_migration_retains_new_diagnostics_before_restoring_fold(self):
        from dotfiles_api.infrastructure.home_migration import HomeMigration
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            (root / "home/.local/bin").mkdir(parents=True)
            (root / "home/.local/bin/command").write_text("new")
            (root / ".local/bin").mkdir(parents=True)
            (root / ".local/bin/personal").write_text("keep")
            home.mkdir()
            (home / ".local").symlink_to(root / ".local")
            migration = HomeMigration(root, home)
            with self.assertRaisesRegex(RuntimeError, "failure"):
                with migration:
                    log = home / ".local/state/diagnostic.log"
                    log.parent.mkdir(parents=True)
                    log.write_text("failure details")
                    raise RuntimeError("failure")
            self.assertTrue((home / ".local").is_symlink())
            retained = migration.backup / "failed-contents/.local/state/diagnostic.log"
            self.assertTrue(retained.is_file(), "Failed migration must retain its diagnostics")
            self.assertEqual(retained.read_text(), "failure details")

    def test_legacy_generated_file_has_a_recoverable_fallback_after_layout_move(self):
        with tempfile.TemporaryDirectory() as temp:
            root, home = Path(temp) / "repo", Path(temp) / "user"
            (root / "home/.config/greetd").mkdir(parents=True)
            (root / "home/.config/greetd/static.conf").write_text("static")
            fallback = root / "templates/legacy/.config/greetd/regreet.css"
            fallback.parent.mkdir(parents=True)
            fallback.write_text("old stylesheet")
            target = home / ".config/greetd"
            target.mkdir(parents=True)
            (target / "regreet.css").symlink_to(root / ".config/greetd/regreet.css")
            from dotfiles_api.infrastructure.home_migration import HomeMigration
            with HomeMigration(root, home):
                self.assertFalse((target / "regreet.css").is_symlink())
                self.assertEqual((target / "regreet.css").read_text(), "old stylesheet")

    def test_source_symlink_cannot_be_written_by_generator_transaction(self):
        from dotfiles_api.application.store import ArtifactStore
        from dotfiles_api.application.transaction import ConfigTransaction
        from dotfiles_api.context.environment import EnvironmentContext
        from dotfiles_api.domain.artifacts import GeneratedArtifact
        from dotfiles_api.infrastructure.file_writer import SystemFileWriter
        with tempfile.TemporaryDirectory() as temp:
            home, repo = Path(temp) / "user", Path(temp) / "repo"
            home.mkdir()
            repo.mkdir()
            tracked = repo / "tracked.conf"
            tracked.write_text("tracked")
            (home / "generated.conf").symlink_to(tracked)
            env = EnvironmentContext(home, repo, "tester")
            transaction = ConfigTransaction(env, ArtifactStore({"test": home / "generated.conf"}), SystemFileWriter())
            with self.assertRaisesRegex(ValueError, "repository"):
                with transaction:
                    transaction.write_artifact(GeneratedArtifact("test", "new"))
            self.assertEqual(tracked.read_text(), "tracked")
