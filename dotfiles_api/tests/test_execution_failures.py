import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.setup import SetupService
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.domain.models import Feature, Profile
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.infrastructure.package_sources.pacman import PacmanSource


class TestExecutionFailures(unittest.TestCase):
    def context(self, code=1, stderr="broken"):
        executor = Mock()
        executor.execute.return_value = CommandResult("", stderr, code)
        return ExecutionContext(False, executor)

    def test_required_nonzero_command_raises(self):
        with self.assertRaisesRegex(RuntimeError, "7"):
            self.context(7).execute(["command"])

    def test_optional_failures_are_explicit_and_return_result(self):
        ctx = self.context()
        self.assertTrue(hasattr(ctx, "optional"))
        with contextlib.redirect_stderr(io.StringIO()):
            result = ctx.optional(["notify-send", "message"])
        self.assertEqual(result.returncode, 1)

    def test_queries_accept_absence_but_not_execution_errors(self):
        ctx = self.context()
        self.assertTrue(hasattr(ctx, "query"))
        self.assertEqual(ctx.query(["pgrep", "waybar"]).returncode, 1)
        with self.assertRaises(RuntimeError):
            self.context(127).query(["missing-tool"])

    def test_real_process_failure_is_not_reported_as_success(self):
        ctx = ExecutionContext(False, SystemCommandExecutor())
        with self.assertRaisesRegex(RuntimeError, "23"):
            ctx.execute([sys.executable, "-c", "raise SystemExit(23)"])

    def test_install_failure_prevents_dependent_setup_steps(self):
        ctx = self.context(9)
        source = PacmanSource(ctx)
        installer = InstallService(None, ctx, PackageRegistry({}), {"pacman": source})
        linker, theme, services, user, extras = (Mock() for _ in range(5))
        setup = SetupService(Mock(), ctx, installer, linker, theme, services, user, extras,
                             graphics_package_detector=lambda: [])
        with patch("shutil.which", return_value="/usr/bin/pacman"), \
                patch("sys.stdin.isatty", return_value=False):
            with self.assertRaises(RuntimeError):
                setup.run_setup()
        linker.link.assert_not_called()
        theme.apply_theme.assert_not_called()
        services.setup_services.assert_not_called()
        user.setup_user.assert_not_called()
        extras.setup_extras.assert_not_called()

    def test_unavailable_package_source_is_an_error(self):
        source = Mock()
        source.is_available.return_value = False
        installer = InstallService(None, None, PackageRegistry({}), {"pacman": source}, inventory=lambda: set())
        with self.assertRaisesRegex(RuntimeError, "pacman"):
            installer.install_profile(Profile("example", [Feature("test", ["git"], [])]))
        source.install.assert_not_called()

    def test_missing_source_is_an_error(self):
        installer = InstallService(None, None, PackageRegistry({}), {}, inventory=lambda: set())
        with self.assertRaisesRegex(RuntimeError, "pacman"):
            installer.install_profile(Profile("example", [Feature("test", ["git"], [])]))

    def test_link_failure_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source", Path(temp) / "target"
            (source / "home").mkdir(parents=True)
            target.mkdir()
            with self.assertRaises(RuntimeError):
                StowLinker(self.context()).link(source, target)

    def test_private_structured_log_and_error_redact_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "state/commands.jsonl"
            executor = Mock()
            secret = "sensitive-value-123"
            executor.execute.return_value = CommandResult("", "rejected " + secret, 5)
            self.assertIn("log_path", ExecutionContext.__dataclass_fields__)
            ctx = ExecutionContext(False, executor, verbose=True, log_path=log)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                with self.assertRaises(RuntimeError) as error:
                    ctx.execute(["tool", "--token", secret], step="install")
            record = json.loads(log.read_text())
            self.assertEqual(record["step"], "install")
            self.assertEqual(record["returncode"], 5)
            self.assertNotIn(secret, log.read_text() + output.getvalue() + str(error.exception))
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)

    def test_dry_run_never_runs_or_writes_log_even_for_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "state/commands.jsonl"
            self.assertIn("log_path", ExecutionContext.__dataclass_fields__)
            executor = Mock()
            ctx = ExecutionContext(True, executor, log_path=log)
            ctx.execute(["tool", "--password=hidden"])
            self.assertFalse(log.parent.exists())
            executor.execute.assert_not_called()

    def test_privileged_commands_refuse_noninteractive_execution(self):
        with patch("sys.stdin.isatty", return_value=False), patch("subprocess.run") as run:
            result = SystemCommandExecutor().execute(["sudo", "true"])
        run.assert_not_called()
        self.assertEqual(result.returncode, 126)
