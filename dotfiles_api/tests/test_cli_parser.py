import unittest
import contextlib
import io
from unittest.mock import patch

from dotfiles_api.presentation import cli


class TestCliParser(unittest.TestCase):
    def parse(self, words):
        self.assertTrue(hasattr(cli, "build_parser"), "CLI needs a reusable real subparser")
        return cli.build_parser().parse_args(words)

    def test_setup_github_is_not_swallowed(self):
        args = self.parse(["setup", "--github"])
        self.assertTrue(args.github)

    def test_configure_theme_is_not_swallowed(self):
        args = self.parse(["configure", "--theme", "shade-raid-dark"])
        self.assertEqual(args.theme, "shade-raid-dark")

    def test_screenshot_receives_region(self):
        args = self.parse(["action", "screenshot", "--region"])
        self.assertEqual(args.action_name, "screenshot")
        self.assertEqual(args.action_args, ["--region"])

    def test_global_options_work_before_or_after_command(self):
        for argv in (["--dry-run", "--verbose", "configure"],
                     ["configure", "--dry-run", "--verbose"],
                     ["--dry-run", "configure", "--verbose"]):
            with self.subTest(argv=argv):
                args = self.parse(argv)
                self.assertTrue(args.dry_run)
                self.assertTrue(args.verbose)

    def test_legacy_theme_position_stays_supported(self):
        args = self.parse(["--theme", "shade-raid-dark", "configure"])
        self.assertEqual(args.theme, "shade-raid-dark")

    def test_missing_action_and_unknown_options_fail(self):
        for argv in (["action"], ["configure", "--theem", "shade-raid-dark"]):
            with self.subTest(argv=argv):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    self.parse(argv)
                self.assertEqual(caught.exception.code, 2)

    def test_login_command_is_explicit(self):
        args = self.parse(["setup-login", "--dry-run"])
        self.assertEqual(args.command, "setup-login")
        self.assertTrue(args.dry_run)

    def test_action_help_exits_before_environment_or_capture(self):
        for words in (["--help", "action", "screenshot"],
                      ["action", "--help", "screenshot"],
                      ["action", "screenshot", "--help"],
                      ["action", "screenshot", "--region", "-h"]):
            with self.subTest(words=words), contextlib.redirect_stdout(io.StringIO()), \
                    patch("dotfiles_api.presentation.cli.Path.home") as home, \
                    patch("dotfiles_api.presentation.cli.EnvironmentContext") as environment, \
                    patch("dotfiles_api.presentation.cli.SystemCommandExecutor") as executor, \
                    patch("dotfiles_api.presentation.cli.ScreenshotAction") as capture:
                with self.assertRaises(SystemExit) as caught:
                    cli.main(words)
                self.assertEqual(caught.exception.code, 0)
                for effect in (home, environment, executor, capture):
                    effect.assert_not_called()

    def test_action_safety_flags_are_global_until_literal_delimiter(self):
        args = self.parse(["action", "screenshot", "--region", "--dry-run", "--verbose"])
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verbose)
        self.assertEqual(args.action_args, ["--region"])
        literal = self.parse(["action", "screenshot", "--", "--dry-run", "--verbose", "--help"])
        self.assertFalse(literal.dry_run)
        self.assertFalse(literal.verbose)
        self.assertEqual(literal.action_args, ["--dry-run", "--verbose", "--help"])

    def test_global_scan_preserves_option_values_and_reports_missing_values(self):
        args = self.parse(["--theme=--dry-run", "configure", "--verbose"])
        self.assertEqual(args.theme, "--dry-run")
        self.assertFalse(args.dry_run)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.parse(["--theme", "--dry-run", "configure"])
        self.assertEqual(caught.exception.code, 2)
        # Future child-specific options must protect their values too.
        parser = cli.build_parser()
        children = next(action.choices for action in parser._actions
                        if hasattr(action, "choices") and isinstance(action.choices, dict))
        children["configure"].add_argument("--output")
        args = parser.parse_args(["configure", "--output=--verbose", "--dry-run"])
        self.assertEqual(args.output, "--verbose")
        self.assertFalse(args.verbose)
        self.assertTrue(args.dry_run)

    def test_semantic_options_are_rejected_outside_their_commands(self):
        for words in (["--github", "configure"], ["reload", "--theme", "dark"],
                      ["action", "screenshot", "--theme", "dark"],
                      ["action", "screenshot", "--github"], ["install", "--theme", "dark"],
                      ["toggle", "--theme", "dark"], ["setup-login", "--github"]):
            with self.subTest(words=words), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as caught:
                self.parse(words)
                self.assertEqual(caught.exception.code, 2)
        self.assertTrue(self.parse(["--github", "setup"]).github)
        self.assertEqual(self.parse(["apply-all", "--theme", "dark"]).theme, "dark")

    def test_duplicate_flags_are_idempotent_but_conflicting_theme_is_rejected(self):
        args = self.parse(["--dry-run", "configure", "--dry-run", "-v", "--verbose",
                           "--theme", "dark", "--theme=dark"])
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verbose)
        self.assertEqual(args.theme, "dark")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.parse(["--theme", "light", "configure", "--theme", "dark"])
        self.assertEqual(caught.exception.code, 2)
