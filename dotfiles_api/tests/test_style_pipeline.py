import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.theme_coordinator import ThemeCoordinator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.domain.events import EventBus
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.theme_styler import ThemeStyler
from dotfiles_api.tests.test_dry_run_safety import snapshot

ROOT = Path(__file__).resolve().parents[2]


class TestStylePipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = EnvironmentContext(Path(self.temp.name), ROOT, "tester")
        self.registry = ApplicationRegistry(APPLICATIONS)
        self.store = ArtifactStore(self.registry.artifact_paths(self.env))
        self.tx = ConfigTransaction(self.env, self.store, SystemFileWriter())
        self.planner = ThemePlanner(self.env, self.store, self.registry.generators(self.tx, EventBus()), self.registry)

    def coordinator(self, executor):
        return ThemeCoordinator(self.env, self.planner, self.tx,
            styler=ThemeStyler(self.env, self.registry, self.store, ExecutionContext(False, executor)))

    def test_dry_run_lists_compilers_without_processes_or_writes(self):
        before = snapshot(self.env.home_dir)
        executor = Mock()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.coordinator(executor).apply(ThemeLoader(self.env).load("shade-raid"), "shade-raid", dry_run=True)
        self.assertIn("Compile 4 stylesheets", output.getvalue())
        executor.execute.assert_not_called()
        self.assertEqual(snapshot(self.env.home_dir), before)

    def test_compiler_failure_prevents_every_theme_write(self):
        executor = Mock()
        executor.execute.return_value = CommandResult("", "invalid SCSS", 1)
        before = snapshot(self.env.home_dir)
        with self.assertRaisesRegex(RuntimeError, "invalid SCSS"), contextlib.redirect_stdout(io.StringIO()):
            self.coordinator(executor).apply(ThemeLoader(self.env).load("shade-raid"), "shade-raid")
        self.assertEqual(snapshot(self.env.home_dir), before)

    @unittest.skipUnless(shutil.which("sassc"), "Requires real sassc")
    def test_all_styles_compile_for_both_themes_and_roll_back_with_colors(self):
        coordinator = self.coordinator(SystemCommandExecutor())
        source = snapshot(ROOT / "home")
        with contextlib.redirect_stdout(io.StringIO()):
            light = coordinator.apply(ThemeLoader(self.env).load("shade-raid"), "shade-raid")
            css = {item.artifact.artifact_id: item.path.read_bytes() for item in light.artifacts
                   if item.artifact.artifact_id in {"waybar-style", "walker-style", "swayosd-style", "wlogout-style"}}
            self.assertEqual(len(css), 4)
            again = coordinator.apply(ThemeLoader(self.env).load("shade-raid"), "shade-raid")
            self.assertFalse(again.changed_generators)
            coordinator.apply(ThemeLoader(self.env).load("shade-raid-dark"), "shade-raid-dark")
            coordinator.rollback()
            for artifact_id, content in css.items():
                self.assertEqual(self.store.resolve_path(artifact_id, "shade-raid").read_bytes(), content)
        self.assertEqual(snapshot(ROOT / "home"), source)

    def test_reloading_does_not_compile_or_replace_generated_css(self):
        from dotfiles_api.infrastructure.reloadables.waybar import WaybarReloadable
        from dotfiles_api.infrastructure.reloadables.wlogout import WlogoutReloadable
        executor = Mock()
        executor.execute.return_value = CommandResult("", "", 0)
        for cls in (WaybarReloadable, WlogoutReloadable):
            cls(ExecutionContext(False, executor)).reload()
        self.assertFalse(any(call.args[0][0] == "sassc" for call in executor.execute.call_args_list))

    def test_source_fingerprint_is_pure_and_changes_with_generated_inputs(self):
        before = snapshot(self.env.home_dir)
        style = next(spec.stylesheets[0] for spec in self.registry.specs if spec.id == "waybar")
        digests = []
        for name in ("shade-raid", "shade-raid-dark"):
            plan = self.planner.build(ThemeLoader(self.env).load(name), name)
            rendered = {item.artifact.artifact_id: item for item in plan.artifacts}
            digests.append(ThemeStyler.source_digest(self.env, style, rendered))
        self.assertNotEqual(*digests)
        self.assertEqual(snapshot(self.env.home_dir), before)
