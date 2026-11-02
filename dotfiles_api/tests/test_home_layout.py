import shutil
import subprocess
import tempfile
import unittest
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
            (old / "static.conf").write_text("old static")
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

    def test_theme_output_paths_never_target_repository(self):
        source = (ROOT / "dotfiles_api/presentation/cli.py").read_text()
        self.assertFalse('env.dotfiles_dir / "plymouth-shade-raid"' in source,
                         "Plymouth output must live outside the repository")

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
