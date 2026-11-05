import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.application.services.doctor import DoctorService
from dotfiles_api.application.services.repair import RepairService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.domain.events import EventBus
from dotfiles_api.domain.models.application_spec import ApplicationSpec
from dotfiles_api.domain.models.output_spec import OutputSpec
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.generators.ghostty import GhosttyGenerator
from dotfiles_api.tests.test_dry_run_safety import snapshot

ROOT = Path(__file__).resolve().parents[2]


class TestDoctorAndRepair(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = EnvironmentContext(Path(self.temp.name), ROOT, "tester")
        selection = self.env.state_dir / "installation.json"
        selection.parent.mkdir(parents=True)
        selection.write_text('{"version": 2, "requested_profiles": ["desktop"], "explicit_packages": []}')
        self.registry = ApplicationRegistry((ApplicationSpec("ghostty", packages=("ghostty",),
            generator=GhosttyGenerator, outputs=(OutputSpec("ghostty-colors", ".config/ghostty/colors.conf"),),
            user_unit="shade-raid-ghostty.service"),))
        self.store = ArtifactStore(self.registry.artifact_paths(self.env))
        self.tx = ConfigTransaction(self.env, self.store, SystemFileWriter())
        self.planner = ThemePlanner(self.env, self.store, self.registry.generators(self.tx, EventBus()), self.registry)
        self.query = Mock(return_value=CommandResult("active\n", "", 0))
        self.doctor = DoctorService(self.env, self.registry, self.planner, FileThemeStore(self.env), self.query,
                                   inventory=lambda: set(), login_dir=Path(self.temp.name) / "etc/greetd")

    def test_missing_dependencies_and_outputs_are_reported_without_writes(self):
        before = snapshot(self.env.home_dir)
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        findings = {item.id: item for item in report.findings}
        self.assertEqual(findings["package:ghostty"].severity, "error")
        self.assertEqual(findings["output:ghostty-colors"].severity, "error")
        self.assertEqual(findings["session"].severity, "unknown")
        self.assertEqual(snapshot(self.env.home_dir), before)
        self.assertEqual(report.exit_code, 1)
        self.assertFalse(any("start" in call.args[0] for call in self.query.call_args_list))

    def test_unavailable_package_inventory_is_reported_unknown(self):
        def unavailable():
            raise RuntimeError('fake unavailable pacman database')
        self.doctor.inventory = unavailable
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == 'packages')
        self.assertEqual(finding.severity, 'unknown')
        self.assertIn('unavailable', finding.message)
        self.assertFalse(any(item.id.startswith('package:') for item in report.findings))

    def test_service_queries_are_read_only_and_failed_service_has_a_plan(self):
        def query(command):
            return CommandResult("inactive", "", 3) if command[0] == "systemctl" else CommandResult("", "", 0)
        self.doctor.query = query
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1", "XDG_CURRENT_DESKTOP": "Hyprland"}):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == "service:shade-raid-ghostty.service")
        self.assertEqual(finding.severity, "unknown")
        self.assertEqual(finding.repair, ())

    def test_plan_id_rejects_new_content_changes_before_apply(self):
        actions = {"configure": Mock()}
        repairs = RepairService(self.doctor, actions)
        with patch.dict(os.environ, {}, clear=True):
            plan = repairs.plan()
            path = self.store.resolve_path("ghostty-colors")
            path.parent.mkdir(parents=True)
            path.write_text("personal edit")
            with self.assertRaisesRegex(ValueError, "changed"), contextlib.redirect_stdout(io.StringIO()):
                repairs.apply(plan.id)
        actions["configure"].assert_not_called()

    def test_invalid_ini_is_reported_without_crashing(self):
        from dotfiles_api.domain.artifacts import GeneratedArtifact
        path = self.store.resolve_path("ghostty-colors").with_suffix(".ini")
        path.parent.mkdir(parents=True)
        path.write_text("not an ini section\n")
        self.store._mappings["ghostty-colors"] = path
        generator = self.planner.generators[0]
        with patch.object(generator, "render", return_value=[GeneratedArtifact("ghostty-colors", "[section]\na=b\n")]), \
                patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == "output:ghostty-colors")
        self.assertEqual(finding.severity, "error")
        self.assertIn("Invalid output", finding.message)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_doctor_fifo_output_returns_promptly(self):
        import subprocess, sys
        script = '''
import os, tempfile
from pathlib import Path
from unittest.mock import patch
from dotfiles_api.tests.test_doctor_and_repair import TestDoctorAndRepair
case = TestDoctorAndRepair(); case.setUp()
try:
    path = case.store.resolve_path("ghostty-colors")
    path.parent.mkdir(parents=True)
    os.mkfifo(path)
    with patch.dict(os.environ, {}, clear=True):
        report = case.doctor.run()
    assert any(item.severity == "error" for item in report.findings)
finally:
    case.doCleanups()
'''
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_doctor_compiled_css_fifo_returns_promptly(self):
        import subprocess, sys
        script = '''
import dataclasses, os
from unittest.mock import patch
from dotfiles_api.tests.test_doctor_and_repair import TestDoctorAndRepair
from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
case = TestDoctorAndRepair(); case.setUp()
try:
    spec = dataclasses.replace(next(s for s in APPLICATIONS if s.id == "waybar"), dependencies=())
    registry = ApplicationRegistry((spec,))
    store = ArtifactStore(registry.artifact_paths(case.env))
    tx = ConfigTransaction(case.env, store, SystemFileWriter())
    case.doctor.applications = registry
    case.doctor.planner = ThemePlanner(case.env, store, registry.generators(tx, EventBus()), registry)
    path = store.resolve_path("waybar-style")
    path.parent.mkdir(parents=True)
    os.mkfifo(path)
    with patch.dict(os.environ, {}, clear=True):
        report = case.doctor.run()
    assert any(item.id == "output:waybar-style" and item.severity == "error" for item in report.findings)
finally:
    case.doCleanups()
'''
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_stow_source_does_not_hide_later_missing_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "repo/home"
            source.mkdir(parents=True)
            (source / "a-broken").symlink_to("missing")
            (source / "z-valid").write_text("content")
            env = EnvironmentContext(root / "user", root / "repo", "tester")
            doctor = DoctorService(env, self.registry, self.planner, self.doctor.theme_store,
                                   self.query, inventory=lambda: set())
            findings = []
            doctor._links(findings)
            self.assertTrue(any(item.severity == "unknown" and "a-broken" in item.id for item in findings))
            self.assertTrue(any(item.severity == "error" and "z-valid" in item.id for item in findings))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_doctor_special_input_files_never_block_and_report_error(self):
        import subprocess, sys
        script = '''
import os
from unittest.mock import patch
from dotfiles_api.tests.test_doctor_and_repair import TestDoctorAndRepair
for relative in (".local/state/shade-raid/installation.json", ".local/state/shade-raid/active-theme", ".config/themes/shade-raid/colors.toml", ".config/themes/style.toml"):
    case = TestDoctorAndRepair(); case.setUp()
    try:
        path = case.env.home_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists(): path.unlink()
        os.mkfifo(path)
        with patch.dict(os.environ, {}, clear=True):
            report = case.doctor.run()
        assert any(item.severity == "error" for item in report.findings), relative
    finally:
        case.doCleanups()
'''
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_active_portal_is_unknown_without_backend_and_interface_checks(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1", "XDG_CURRENT_DESKTOP": "Hyprland"}):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == "service:xdg-desktop-portal.service")
        self.assertEqual(finding.severity, "unknown")
        self.assertIn("backend", finding.message.lower())

    def test_clean_tracked_files_claim_does_not_claim_untracked_are_clean(self):
        self.doctor.query = Mock(return_value=CommandResult("", "", 0))
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == "git")
        self.assertIn("tracked", finding.message.lower())

    def test_private_state_audit_finds_symlinks_and_public_modes(self):
        state = self.env.state_dir
        state.mkdir(parents=True, exist_ok=True)
        state.chmod(0o755)
        backup = state / "transactions/one/backups"
        backup.mkdir(parents=True, mode=0o700)
        secret = backup / "0"
        secret.write_text("private")
        secret.chmod(0o644)
        (state / "preview-theme").symlink_to("missing")
        findings = []
        self.doctor._permissions(findings)
        messages = "\n".join(item.message for item in findings)
        self.assertIn(str(state), messages)
        self.assertIn(str(secret), messages)
        self.assertIn(str(state / "preview-theme"), messages)

    def test_login_audit_flags_broken_symlink_and_insecure_background(self):
        self.doctor.login_dir.mkdir(parents=True)
        broken = self.doctor.login_dir / "config.toml"
        broken.symlink_to("gone")
        background = self.doctor.login_dir / "regreet-background.jpg"
        background.write_bytes(b"fake")
        background.chmod(0o666)
        findings = []
        self.doctor._permissions(findings)
        self.assertTrue(any(item.id == "login:config.toml" and item.severity == "error" for item in findings))
        self.assertTrue(any(item.id == "login:regreet-background.jpg" and item.severity == "error" for item in findings))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_real_doctor_json_reports_fifo_with_matching_exit_status(self):
        import json, subprocess, sys
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            state = home / ".local/state/shade-raid"
            state.mkdir(parents=True)
            os.mkfifo(state / "installation.json")
            env = {**os.environ, "HOME": temp, "DOTFILES_DIR": str(ROOT),
                   "XDG_STATE_HOME": str(home / ".local/state"), "XDG_RUNTIME_DIR": str(home / ".runtime")}
            env.pop("WAYLAND_DISPLAY", None)
            result = subprocess.run([sys.executable, "-m", "dotfiles_api.presentation.cli", "doctor", "--json"],
                                    env=env, capture_output=True, text=True, timeout=15)
            report = json.loads(result.stdout)
            self.assertEqual(report["exit_code"], 1)
            self.assertEqual(result.returncode, report["exit_code"])
            self.assertTrue(any(item["id"] == "selection" and item["severity"] == "error" for item in report["findings"]))

    def test_query_io_failure_becomes_unknown_without_aborting_json_report(self):
        self.doctor.query = Mock(side_effect=OSError("not available"))
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1", "XDG_CURRENT_DESKTOP": "Hyprland"}):
            report = self.doctor.run()
        by_id = {item.id: item for item in report.findings}
        self.assertEqual(by_id["service:shade-raid-ghostty.service"].severity, "unknown")
        self.assertEqual(by_id["git"].severity, "unknown")
        self.assertEqual(report.to_dict()["version"], 1)

    def test_installation_selection_uses_current_profiles_and_explicit_packages(self):
        import json
        selection = self.env.state_dir / "installation.json"
        selection.parent.mkdir(parents=True, exist_ok=True)
        selection.write_text(json.dumps({"version": 2, "requested_profiles": ["core"],
                                         "explicit_packages": [], "profiles": ["desktop"],
                                         "packages": ["obsolete-package"], "optional_packages": []}))
        from dataclasses import replace
        spec = replace(self.registry.specs[0], profiles=("core",))
        self.doctor.applications = ApplicationRegistry((spec,))
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        ids = {item.id for item in report.findings}
        self.assertIn("package:ghostty", ids)
        self.assertNotIn("package:obsolete-package", ids)

    def test_fresh_home_does_not_claim_desktop_is_installed_and_broken(self):
        (self.env.state_dir / "installation.json").unlink()
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        self.assertTrue(any(item.id == "selection" and item.severity == "unknown" for item in report.findings))
        self.assertFalse(any(item.id.startswith(("package:", "output:", "link:")) for item in report.findings))

    def test_inactive_service_is_unknown_without_reason_or_unsafe_repair(self):
        def query(command):
            return CommandResult("inactive", "", 3) if command[0] == "systemctl" else CommandResult("", "", 0)
        self.doctor.query = query
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1", "XDG_CURRENT_DESKTOP": "Hyprland"}):
            report = self.doctor.run()
        finding = next(item for item in report.findings if item.id == "service:shade-raid-ghostty.service")
        self.assertEqual(finding.severity, "unknown")
        self.assertEqual(finding.repair, ())

    def test_login_audit_flags_legacy_sudoers_and_incomplete_installation(self):
        etc = self.doctor.login_dir.parent
        self.doctor.login_dir.mkdir(parents=True)
        (self.doctor.login_dir / "regreet.toml").write_text("[background]\n")
        sudoers = etc / "sudoers.d"
        sudoers.mkdir()
        (sudoers / "shade-raid").symlink_to("missing")
        findings = []
        self.doctor._permissions(findings)
        by_id = {item.id: item for item in findings}
        self.assertEqual(by_id["login:config.toml"].severity, "error")
        self.assertEqual(by_id["sudoers:shade-raid"].severity, "error")
        self.assertTrue(by_id["sudoers:shade-raid"].privileged)

    def test_repair_plan_describes_automatic_operation_effects_and_paths(self):
        with patch.dict(os.environ, {}, clear=True):
            plan = RepairService(self.doctor, {}).plan()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            plan.describe()
        text = output.getvalue()
        self.assertIn(str(self.store.resolve_path("ghostty-colors")), text)
        self.assertIn(str(self.env.state_dir / "transactions"), text)
        self.assertIn("refresh", text.lower())
        self.assertIn("wallpaper", text.lower())

    def test_incomplete_setup_is_not_reported_as_complete(self):
        import json
        selection = self.env.state_dir / "installation.json"
        selection.write_text(json.dumps({"version": 2, "requested_profiles": ["desktop"],
                                         "explicit_packages": [], "package_status": "failed_or_partial",
                                         "desktop_configuration_status": "in_progress"}))
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run()
        by_id = {item.id: item for item in report.findings}
        self.assertEqual(by_id["setup:packages"].severity, "error")
        self.assertIn("failed_or_partial", by_id["setup:packages"].message)
        self.assertEqual(by_id["setup:configuration"].severity, "error")

    def test_repair_rechecks_next_operation_after_prior_action(self):
        from dotfiles_api.domain.models.diagnostic import Diagnostic
        from dotfiles_api.domain.models.diagnostic_report import DiagnosticReport
        stable = DiagnosticReport((Diagnostic("link:a", "error", "missing", ("link",), evidence="old"),
                                   Diagnostic("output:a", "error", "stale", ("configure",), evidence="old")))
        changed = DiagnosticReport((stable.findings[0], Diagnostic("output:a", "error", "personal edit", ("configure",), evidence="new")))
        doctor = Mock()
        doctor.run.side_effect = [stable, stable, stable, changed]
        actions = {"link": Mock(), "configure": Mock()}
        repair = RepairService(doctor, actions)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "changed"):
                repair.apply(repair.plan().id)
        actions["link"].assert_called_once()
        actions["configure"].assert_not_called()

    def test_privileged_fixes_are_never_executed(self):
        self.doctor.login_dir.mkdir(parents=True)
        path = self.doctor.login_dir / "regreet.toml"
        path.write_text("example")
        path.chmod(0o666)
        actions = {"configure": Mock(), "setup-login": Mock()}
        repairs = RepairService(self.doctor, actions)
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            plan = repairs.plan()
            self.assertTrue(any(item.privileged for item in plan.operations))
            repairs.apply(plan.id)
        actions["setup-login"].assert_not_called()
        self.assertEqual(path.stat().st_mode & 0o777, 0o666)

    def test_dry_run_doctor_and_repair_start_no_processes_or_state(self):
        before = snapshot(self.env.home_dir)
        report = self.doctor.run(dry_run=True)
        self.assertTrue(report.findings)
        self.query.assert_not_called()
        self.assertEqual(snapshot(self.env.home_dir), before)

    def test_parser_requires_explicit_repair_apply_and_supports_json(self):
        from dotfiles_api.presentation.cli import build_parser
        args = build_parser().parse_args(["doctor", "--json"])
        self.assertTrue(args.json)
        args = build_parser().parse_args(["repair", "--plan"])
        self.assertFalse(args.apply)

    def test_real_cli_diagnostics_never_create_logs_locks_or_processes(self):
        import json
        from dotfiles_api.presentation.cli import main
        for words in (["doctor", "--json"], ["repair", "--plan"], ["doctor", "--dry-run"],
                      ["repair", "--apply", "--dry-run"]):
            with self.subTest(words=words), tempfile.TemporaryDirectory() as temp:
                home = Path(temp)
                variables = {"DOTFILES_DIR": str(ROOT), "XDG_STATE_HOME": str(home / ".state"),
                             "XDG_RUNTIME_DIR": str(home / ".runtime")}
                with patch.dict(os.environ, variables), patch("pathlib.Path.home", return_value=home), \
                        patch("subprocess.Popen") as process, \
                        patch("dotfiles_api.infrastructure.executor.SystemCommandExecutor.execute", return_value=CommandResult("", "", 0)) as query, \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    main(words)
                if "--json" in words:
                    self.assertIn("findings", json.loads(output.getvalue()))
                self.assertEqual(list(home.iterdir()), [])
                process.assert_not_called()
                self.assertTrue(all(call.args[0][0] in {"git", "systemctl"} for call in query.call_args_list))
                if "--dry-run" in words:
                    query.assert_not_called()

    def test_core_only_selection_does_not_diagnose_absent_desktop_outputs(self):
        import json
        selection = self.env.state_dir / "installation.json"
        selection.parent.mkdir(parents=True, exist_ok=True)
        selection.write_text(json.dumps({"profiles": ["core"], "packages": [], "optional_packages": []}))
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run(dry_run=True)
        self.assertFalse(any(item.id.startswith("output:") for item in report.findings))

    def test_explicit_optional_package_gets_output_checks_without_its_whole_profile(self):
        import dataclasses
        import json
        optional = dataclasses.replace(self.registry.specs[0], profiles=("daily",), required=False)
        self.doctor.applications = ApplicationRegistry((optional,))
        selection = self.env.state_dir / "installation.json"
        selection.parent.mkdir(parents=True, exist_ok=True)
        selection.write_text(json.dumps({"profiles": ["desktop"], "packages": ["ghostty"], "optional_packages": ["ghostty"]}))
        with patch.dict(os.environ, {}, clear=True):
            report = self.doctor.run(dry_run=True)
        self.assertTrue(any(item.id == "output:ghostty-colors" for item in report.findings))

    def test_cli_apply_without_reviewed_id_creates_no_lock(self):
        from dotfiles_api.presentation.cli import main
        with tempfile.TemporaryDirectory() as temp, patch("pathlib.Path.home", return_value=Path(temp)), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["repair", "--apply"])
            self.assertEqual(list(Path(temp).iterdir()), [])

    @unittest.skipUnless(shutil.which("sassc"), "Requires real Sass compilation")
    def test_compiled_css_tampering_is_detected_without_recompiling_or_writing(self):
        import dataclasses
        from dotfiles_api.application.theme_coordinator import ThemeCoordinator
        from dotfiles_api.context.execution import ExecutionContext
        from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
        from dotfiles_api.infrastructure.executor import SystemCommandExecutor
        from dotfiles_api.infrastructure.theme_styler import ThemeStyler
        spec = dataclasses.replace(next(spec for spec in APPLICATIONS if spec.id == "waybar"), dependencies=())
        registry = ApplicationRegistry((spec,))
        store = ArtifactStore(registry.artifact_paths(self.env))
        tx = ConfigTransaction(self.env, store, SystemFileWriter())
        planner = ThemePlanner(self.env, store, registry.generators(tx, EventBus()), registry)
        styler = ThemeStyler(self.env, registry, store, ExecutionContext(False, SystemCommandExecutor()))
        with contextlib.redirect_stdout(io.StringIO()):
            ThemeCoordinator(self.env, planner, tx, styler).apply(ThemeLoader(self.env).load("shade-raid"), "shade-raid")
        doctor = DoctorService(self.env, registry, planner, FileThemeStore(self.env), self.query,
                               inventory=lambda: set(), login_dir=self.doctor.login_dir)
        with patch.dict(os.environ, {}, clear=True):
            report = doctor.run()
        self.assertEqual(next(item for item in report.findings if item.id == "output:waybar-style").severity, "ok")
        path = store.resolve_path("waybar-style")
        path.write_text(path.read_text() + "\n/* personal CSS edit */\n")
        before = snapshot(self.env.home_dir)
        with patch.dict(os.environ, {}, clear=True), patch("subprocess.Popen") as process:
            report = doctor.run()
        process.assert_not_called()
        self.assertNotEqual(next(item for item in report.findings if item.id == "output:waybar-style").severity, "ok")
        self.assertEqual(snapshot(self.env.home_dir), before)
