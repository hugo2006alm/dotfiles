import dataclasses
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_install_dependencies_are_added_for_selected_optional_application(self):
        dependency = ApplicationSpec("engine", packages=("engine",), required=False, profiles=())
        runtime = ApplicationSpec("session", packages=("session",), required=False, profiles=())
        app = ApplicationSpec("optional", packages=("optional",), dependencies=("engine",),
                              runtime_dependencies=("session",), required=False, profiles=())
        specs = (dependency, runtime, app)
        registry = ApplicationRegistry(specs)
        self.assertEqual([spec.id for spec in registry.installation_specs([], ["optional"])], ["engine", "optional"])
        with patch("dotfiles_api.infrastructure.application_catalog.APPLICATIONS", specs):
            from dotfiles_api.application.profiles.desktop import build_desktop_profile
            profile = build_desktop_profile(optional_packages=["optional"], graphics_packages=["mesa"])
        self.assertIn("engine", profile.get_packages())
        self.assertIn("optional", profile.get_packages())
        self.assertNotIn("session", profile.get_packages())

    def test_rejects_conflicting_sources_unless_explicitly_overridden(self):
        a = ApplicationSpec("a", packages=("x",))
        b = ApplicationSpec("b", packages=("x",), package_sources=(("x", "yay"),))
        with self.assertRaisesRegex(ValueError, "Conflicting package sources"):
            ApplicationRegistry((a, b))
        self.assertEqual(ApplicationRegistry((a, b), source_overrides={"x": "yay"}).package_sources(), {"x": "yay"})

    def test_reload_contract_rejects_invalid_strategies(self):
        factory = lambda *args: object()
        cases = (ApplicationSpec("a", reload_strategy="typo"),
                 ApplicationSpec("a", reload_factory=factory),
                 ApplicationSpec("a", reload_strategy="application"),
                 ApplicationSpec("a", reload_strategy="systemd-user-restart"),
                 ApplicationSpec("a", user_unit="../../unsafe.service"))
        for spec in cases:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                ApplicationRegistry((spec,))
        ApplicationRegistry((ApplicationSpec("a", user_unit="example.service", reload_strategy="systemd-user-restart"),))

    def test_uninstalled_optional_app_does_not_get_a_reload_handler(self):
        optional = ApplicationSpec("optional", required=False, runtime_executables=("absent-app",),
                                   reload_factory=lambda *args: "handler", reload_strategy="application")
        registry = ApplicationRegistry((optional,))
        with patch("dotfiles_api.application.application_registry.shutil.which", return_value=None):
            self.assertEqual(registry.reloadables(None, None, None, None), [])
        with patch("dotfiles_api.application.application_registry.shutil.which", return_value="/usr/bin/absent-app"):
            self.assertEqual(registry.reloadables(None, None, None, None), ["handler"])

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

    def test_stylesheet_input_mapping_rejects_escapes_and_collisions(self):
        from dotfiles_api.domain.models.stylesheet_spec import StylesheetSpec
        for mappings in ((("input", "../outside.scss"),), (("input", "/etc/passwd"),),
                         (("input", "style.scss"),), (("other", "nested.scss"),),
                         (("input", "a.scss"), ("input", "b.scss"))):
            style = StylesheetSpec("dir/style.scss", "css", ("input",), mappings)
            spec = ApplicationSpec("app", outputs=(OutputSpec("input", "input.scss"), OutputSpec("css", "style.css")), stylesheets=(style,))
            with self.subTest(mappings=mappings), self.assertRaisesRegex(ValueError, "input mapping"):
                ApplicationRegistry((spec,))

    def test_generator_cannot_silently_omit_or_add_outputs(self):
        from types import SimpleNamespace
        spec = ApplicationSpec("a", outputs=(OutputSpec("expected", "expected"),))
        registry = ApplicationRegistry((spec,))
        generator = SimpleNamespace(name="a", render=lambda tokens, theme: [])
        with self.assertRaisesRegex(ValueError, "outputs"):
            registry.validate_outputs([generator], None, "test")

    def test_rejects_invalid_stylesheet_contracts(self):
        from dotfiles_api.domain.models.stylesheet_spec import StylesheetSpec
        for style in (StylesheetSpec("../escape.scss", "css", ("scss",)),
                      StylesheetSpec("style.scss", "missing", ("scss",)),
                      StylesheetSpec("style.scss", "css", ("missing",))):
            with self.subTest(style=style), self.assertRaises(ValueError):
                ApplicationRegistry((ApplicationSpec("a", outputs=(OutputSpec("scss", "colors.scss"),
                    OutputSpec("css", "style.css")), stylesheets=(style,)),))
