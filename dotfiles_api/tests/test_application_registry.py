import dataclasses
import tempfile
import unittest
from pathlib import Path

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.domain.models.application_spec import ApplicationSpec
from dotfiles_api.domain.models.output_spec import OutputSpec
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS


class TestApplicationRegistry(unittest.TestCase):
    def test_rejects_duplicate_ids_missing_dependencies_and_cycles(self):
        a = ApplicationSpec("a")
        for specs in ((a, a), (dataclasses.replace(a, dependencies=("missing",)),),
                      (dataclasses.replace(a, dependencies=("b",)), ApplicationSpec("b", dependencies=("a",)))):
            with self.subTest(specs=specs), self.assertRaises(ValueError):
                ApplicationRegistry(specs)

    def test_rejects_ambiguous_and_unsafe_outputs(self):
        for output in (OutputSpec("x", "../escape"), OutputSpec("x", "/etc/x")):
            with self.subTest(output=output), self.assertRaises(ValueError):
                ApplicationRegistry((ApplicationSpec("a", outputs=(output,)),))
        with self.assertRaises(ValueError):
            ApplicationRegistry((ApplicationSpec("a", outputs=(OutputSpec("x", "a"),)),
                                 ApplicationSpec("b", outputs=(OutputSpec("x", "b"),))))
        with self.assertRaises(ValueError):
            ApplicationRegistry((ApplicationSpec("a", outputs=(OutputSpec("x", "same"), OutputSpec("y", "same"))),))

    def test_extension_provides_packages_paths_and_generation_without_cli_edits(self):
        registry = ApplicationRegistry((ApplicationSpec("custom", packages=("custom-package",),
            package_sources=(("custom-package", "yay"),),
            outputs=(OutputSpec("custom-output", ".config/custom/result.css"),)),))
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / "repo", "tester")
            self.assertEqual(registry.artifact_paths(env)["custom-output"], Path(temp) / ".config/custom/result.css")
        self.assertEqual(registry.packages("desktop"), ["custom-package"])
        self.assertEqual(registry.package_sources(), {"custom-package": "yay"})

    def test_catalog_covers_actual_generator_outputs_for_both_themes(self):
        from dotfiles_api.application.loader import ThemeLoader
        from dotfiles_api.application.store import ArtifactStore
        from dotfiles_api.application.transaction import ConfigTransaction
        from dotfiles_api.domain.events import EventBus
        from dotfiles_api.infrastructure.file_writer import SystemFileWriter
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), root, "tester")
            registry = ApplicationRegistry(APPLICATIONS)
            store = ArtifactStore(registry.artifact_paths(env))
            tx = ConfigTransaction(env, store, SystemFileWriter(), dry_run=True)
            generators = registry.generators(tx, EventBus())
            for theme in ("shade-raid", "shade-raid-dark"):
                tokens = ThemeLoader(env).load(theme)
                registry.validate_outputs(generators, tokens, theme)
            self.assertEqual({g.name for g in generators}, {s.id for s in APPLICATIONS if s.generator})

    def test_generator_cannot_silently_omit_or_add_outputs(self):
        from types import SimpleNamespace
        spec = ApplicationSpec("a", outputs=(OutputSpec("expected", "expected"),))
        registry = ApplicationRegistry((spec,))
        generator = SimpleNamespace(name="a", render=lambda tokens, theme: [])
        with self.assertRaisesRegex(ValueError, "outputs"):
            registry.validate_outputs([generator], None, "test")
