import unittest
import contextlib
import io

from dotfiles_api.presentation import cli


class TestCliParser(unittest.TestCase):
    def parse(self, words):
        self.assertTrue(hasattr(cli, "build_parser"), "CLI needs a reusable real subparser")
        return cli.build_parser().parse_args(words)

    def test_setup_github_is_not_swallowed(self):
        args = self.parse(["setup", "--github"])
        self.assertTrue(args.github)

    def test_setup_ssh_server_option_is_explicit(self):
        self.assertFalse(self.parse(["setup"]).ssh_server)
        self.assertTrue(self.parse(["setup", "--ssh-server"]).ssh_server)

    def test_configure_theme_is_not_swallowed(self):
        args = self.parse(["configure", "--theme", "shade-raid-dark"])
        self.assertEqual(args.theme, "shade-raid-dark")

    def test_screenshot_receives_region(self):
        args = self.parse(["action", "screenshot", "--region"])
        self.assertEqual(args.action_name, "screenshot")
        self.assertEqual(args.action_args, ["--region"])

    def test_dry_run_after_action_arguments_is_still_global(self):
        args = self.parse(["action", "screenshot", "--region", "--dry-run"])
        self.assertTrue(args.dry_run)
        self.assertEqual(args.action_args, ["--region"])

    def test_explicit_delimiter_preserves_action_flags(self):
        args = self.parse(["action", "screenshot", "--", "--dry-run"])
        self.assertFalse(args.dry_run)
        self.assertEqual(args.action_args, ["--dry-run"])

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
