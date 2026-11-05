import contextlib
import fcntl
import io
import json
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.reload import ReloadService
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.domain.events import ConfigGeneratedEvent
from dotfiles_api.domain.models import Feature, Profile
from dotfiles_api.infrastructure.executor import SystemCommandExecutor


class TestExecutionContracts(unittest.TestCase):
    def test_reload_failures_are_aggregated_after_every_required_attempt(self):
        calls = []
        failing, success, failing_again = Mock(), Mock(), Mock()
        def fail_first():
            calls.append("first")
            raise RuntimeError("first failed")
        def fail_third():
            calls.append("third")
            raise RuntimeError("third failed")
        failing.reload.side_effect = fail_first
        success.reload.side_effect = lambda: calls.append("second")
        failing_again.reload.side_effect = fail_third
        with self.assertRaisesRegex(RuntimeError, "2 required"):
            ReloadService([failing, success, failing_again]).reload_all()
        self.assertEqual(calls, ["first", "second", "third"])

    def test_optional_reload_is_reported_without_failing_other_refreshes(self):
        optional, required = Mock(), Mock()
        optional.reload.side_effect = RuntimeError("optional failed")
        with contextlib.redirect_stderr(io.StringIO()) as output:
            ReloadService([optional, required], optional_reloadables=[optional]).reload_all()
        required.reload.assert_called_once()
        self.assertIn("OPTIONAL", output.getvalue())

    def test_event_reload_failure_is_synchronous_and_visible(self):
        reloadable = SimpleNamespace(supports=lambda name: True,
                                     reload=Mock(side_effect=RuntimeError("refresh failed")))
        with self.assertRaisesRegex(RuntimeError, "required"):
            ReloadService([reloadable]).handle_config_generated(ConfigGeneratedEvent(generator_name="test"))

    def test_facade_reload_propagates_failure_for_cli_exit_handling(self):
        from dotfiles_api.application.facade import DotfilesFacade
        reloader = Mock()
        reloader.reload.side_effect = RuntimeError("refresh failed")
        facade = DotfilesFacade(Mock(), Mock(), Mock(), Mock(), ReloadService([reloader]), Mock())
        with self.assertRaises(RuntimeError):
            facade.reload()

    def test_cli_configure_observes_required_refresh_failure(self):
        from dotfiles_api.presentation.cli import main
        with contextlib.ExitStack() as stack:
            facade = stack.enter_context(patch("dotfiles_api.presentation.cli.DotfilesFacade"))
            stack.enter_context(patch("dotfiles_api.presentation.cli.ActionService"))
            stack.enter_context(patch("dotfiles_api.presentation.cli.open", mock_open(), create=True))
            stack.enter_context(patch("fcntl.flock"))
            stack.enter_context(patch("os.remove"))
            stack.enter_context(patch("atexit.register"))
            popen = stack.enter_context(patch("subprocess.Popen"))
            facade.return_value.apply_theme.side_effect = RuntimeError("required refresh failed")
            with self.assertRaisesRegex(RuntimeError, "required refresh"):
                main(["configure"])
            popen.assert_not_called()

    def test_busy_cross_process_reload_is_not_reported_as_success(self):
        reloadable = Mock()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reload-Mock.lock"
            with path.open("a") as held:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaisesRegex(RuntimeError, "required"):
                    ReloadService([reloadable], runtime_dir=Path(temp)).reload_all()
        reloadable.reload.assert_not_called()

    def test_spawn_returns_while_real_child_is_alive_without_captured_pipes(self):
        context = ExecutionContext(False, SystemCommandExecutor())
        start = time.monotonic()
        script = "import sys,time; sys.stdout.write('x'*1000000); sys.stderr.write('x'*1000000); time.sleep(30)"
        process = context.spawn([sys.executable, "-c", script], step="launch:test")
        try:
            self.assertLess(time.monotonic() - start, 2)
            self.assertIsNone(process.poll())
            self.assertIsNone(process.stdout)
            self.assertIsNone(process.stderr)
        finally:
            process.terminate()
            process.wait(timeout=2)

    def test_spawn_reports_immediate_real_child_failure_without_private_output(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "commands.jsonl"
            context = ExecutionContext(False, SystemCommandExecutor(), verbose=True, log_path=log)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaisesRegex(RuntimeError, "29") as error:
                    context.spawn([sys.executable, "-c", "import sys; print('FAKE_PRIVATE', file=sys.stderr); sys.exit(29)"])
            self.assertNotIn("FAKE_PRIVATE", output.getvalue() + log.read_text() + str(error.exception))
            self.assertEqual(json.loads(log.read_text())["returncode"], 29)

    def test_spawn_dry_run_never_calls_executor_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            executor = Mock()
            context = ExecutionContext(True, executor, log_path=Path(temp) / "state/log")
            self.assertIsNone(context.spawn(["firefox", "https://example.invalid/?token=FAKE_DRY"]))
            executor.spawn.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_spawn_refuses_interactive_commands_before_process_creation(self):
        with patch("subprocess.Popen") as popen:
            for command in (["sudo", "true"], ["yay", "-S", "fake"], ["su"], ["gh", "auth", "login"], ["chsh"]):
                with self.subTest(command=command), self.assertRaises(RuntimeError):
                    ExecutionContext(False, SystemCommandExecutor()).spawn(command)
            popen.assert_not_called()

    def test_log_failure_preserves_success_and_real_failure_status(self):
        with tempfile.TemporaryDirectory() as temp:
            blocker = Path(temp) / "file"
            blocker.write_text("not a directory")
            for code in (0, 17):
                executor = Mock()
                executor.execute.return_value = CommandResult("done", "failed safely", code)
                context = ExecutionContext(False, executor, log_path=blocker / "commands.jsonl")
                with contextlib.redirect_stderr(io.StringIO()) as output:
                    if code:
                        with self.assertRaisesRegex(RuntimeError, "17"):
                            context.execute(["tool"])
                    else:
                        self.assertEqual(context.execute(["tool"]).stdout, "done")
                self.assertIn("OBSERVABILITY", output.getvalue())
                self.assertNotIn(str(blocker), output.getvalue())

    def test_log_guard_rejects_symlink_into_repository_without_changing_operation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, home = root / "repo", root / "home"
            repo.mkdir()
            home.mkdir()
            (home / "state").symlink_to(repo, target_is_directory=True)
            def guard(path):
                if path.resolve().is_relative_to(repo):
                    raise ValueError("FAKE_PRIVATE_GUARD")
            executor = Mock()
            executor.execute.return_value = CommandResult("done", "", 0)
            context = ExecutionContext(False, executor, log_path=home / "state/commands.jsonl", output_guard=guard)
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(context.execute(["tool"]).stdout, "done")
            executor.execute.assert_called_once()
            self.assertEqual(list(repo.iterdir()), [])
            self.assertNotIn("FAKE_PRIVATE_GUARD", output.getvalue())
            self.assertIn("OBSERVABILITY", output.getvalue())

    def test_opaque_oauth_fragment_and_shell_variants_fail_closed(self):
        from dotfiles_api.context.command_logging import redacted_diagnostics
        cases = [
            (["tool", "https://example.invalid/#access_token=FAKE_FRAGMENT"], "FAKE_FRAGMENT"),
            (["tool", "https://example.invalid/reset/FAKE_PATH_TOKEN?code=FAKE_CODE"], "FAKE_PATH_TOKEN"),
            (["bash", "-euc", "echo FAKE_SCRIPT"], "FAKE_SCRIPT"),
        ]
        for args, stderr in cases:
            with self.subTest(args=args):
                command, diagnostic = redacted_diagnostics(args, stderr)
                self.assertNotIn("FAKE_", command + diagnostic)

    def test_failed_spawn_does_not_chain_private_oserror(self):
        executor = Mock()
        executor.spawn.side_effect = OSError("FAKE_PRIVATE_OSERROR")
        command = ["launcher", "FAKE_PRIVATE_ARG"]
        try:
            ExecutionContext(False, executor).spawn(command)
        except RuntimeError:
            self.assertNotIn("FAKE_PRIVATE", traceback.format_exc())
        else:
            self.fail("Spawn failure must be observable")

    def test_all_source_preflights_finish_before_install_and_label_failure(self):
        first, second = Mock(), Mock()
        first.is_available.return_value = True
        second.is_available.return_value = False
        service = InstallService(None, None, PackageRegistry({"extra": "yay"}), {"pacman": first, "yay": second})
        with self.assertRaisesRegex(RuntimeError, "no installation commands attempted"):
            service.install_profile(Profile("test", [Feature("test", ["git", "extra"], [])]))
        first.install.assert_not_called()
        second.install.assert_not_called()

    def test_private_and_detected_arguments_never_reach_observable_surfaces(self):
        cases = [
            (["firefox", "https://example.invalid/reset?token=FAKE_URL#FAKE_FRAGMENT"], "FAKE_URL FAKE_FRAGMENT", False),
            (["tool", "-H", "Authorization: Bearer FAKE_HEADER"], "Authorization: Bearer FAKE_HEADER", False),
            (["tool", "https://FAKE_USER:FAKE_PASS@example.invalid/callback?code=FAKE_CODE#FAKE_HASH"], "FAKE_PASS FAKE_CODE", False),
            (["sh", "-c", "echo FAKE_SHELL"], "FAKE_SHELL", False),
            (["wl-paste", "--no-newline"], "FAKE_CLIPBOARD", False),
            (["custom-launcher", "FAKE_ARGUMENT"], "FAKE_DIAGNOSTIC", True),
        ]
        for args, diagnostic, sensitive in cases:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as temp:
                log = Path(temp) / "commands.jsonl"
                executor = Mock()
                executor.execute.return_value = CommandResult("", diagnostic, 8)
                context = ExecutionContext(False, executor, verbose=True, log_path=log)
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    with self.assertRaises(RuntimeError) as error:
                        context.execute(args, sensitive=sensitive)
                observable = output.getvalue() + log.read_text() + str(error.exception)
                self.assertNotIn("FAKE_", observable)

    def test_interactive_failure_has_inherited_stdio_and_honest_diagnostics(self):
        with patch("sys.stdin.isatty", return_value=True), patch("subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(["gh"], 13)
            result = SystemCommandExecutor().execute(["gh", "auth", "login"])
        self.assertFalse(run.call_args.kwargs["capture_output"])
        self.assertFalse(result.output_captured)
        executor = Mock()
        executor.execute.return_value = result
        with self.assertRaisesRegex(RuntimeError, "stderr was not captured"):
            ExecutionContext(False, executor).execute(["gh", "auth", "login"])

    def test_second_install_group_failure_reports_completed_and_uncertain_effects(self):
        first, second = Mock(), Mock()
        first.is_available.return_value = second.is_available.return_value = True
        second.install.side_effect = RuntimeError("fake manager failure")
        service = InstallService(None, None, PackageRegistry({"extra": "yay"}), {"pacman": first, "yay": second})
        profile = Profile("test", [Feature("test", ["git", "extra"], [])])
        with self.assertRaises(RuntimeError) as error:
            service.install_profile(profile)
        first.install.assert_called_once_with(["git"])
        self.assertEqual(error.exception.completed_groups, (("pacman", ("git",)),))
        self.assertEqual(error.exception.failed_source, "yay")
        self.assertIn("may have partial effects", str(error.exception))
        self.assertIn("not rolled back", str(error.exception))
