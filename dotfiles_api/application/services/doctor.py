import hashlib
import json
import os
import stat
from pathlib import Path

from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.profiles.software import SoftwareProfileResolver
from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.domain.models.diagnostic import Diagnostic
from dotfiles_api.domain.models.diagnostic_report import DiagnosticReport
from dotfiles_api.infrastructure.package_inventory import PackageInventory
from dotfiles_api.infrastructure.safe_file import read_regular_file


class DoctorService:
    """Inspect desired/actual state. Queries bypass ExecutionContext's write logs."""

    def __init__(self, env, applications, planner, theme_store, query, inventory=None, login_dir=Path("/etc/greetd")):
        self.env, self.applications, self.planner, self.theme_store = env, applications, planner, theme_store
        self.query, self.inventory, self.login_dir = query, inventory or PackageInventory().names, login_dir

    def run(self, dry_run=False):
        findings = []
        wayland = bool(os.environ.get("WAYLAND_DISPLAY") and os.environ.get("XDG_CURRENT_DESKTOP"))
        findings.append(Diagnostic("session", "ok" if wayland else "unknown",
                                   "Wayland session detected" if wayland else "Outside Wayland: live service checks deferred"))
        selected, optional, desired = [], [], []
        selection = self.env.state_dir / "installation.json"
        try:
            raw_selection = read_regular_file(selection)
            if raw_selection is None:
                findings.append(Diagnostic("selection", "unknown", "No saved installation selection; setup status is unknown"))
            else:
                data = json.loads(raw_selection)
                for key in ("profiles", "packages", "optional_packages", "requested_profiles", "explicit_packages"):
                    if not isinstance(data.get(key, []), list) or not all(isinstance(value, str) for value in data.get(key, [])):
                        raise ValueError(f"invalid {key}")
                selected = data.get("requested_profiles", data.get("profiles", []))
                optional = data.get("explicit_packages", data.get("optional_packages", []))
                if not selected and not optional:
                    findings.append(Diagnostic("selection", "unknown", "Saved installation has no recorded profile or package choices"))
                for field, finding_id in (("package_status", "setup:packages"),
                                          ("desktop_configuration_status", "setup:configuration")):
                    status = data.get(field, "not_recorded")
                    if status in {"in_progress", "failed", "failed_or_partial"}:
                        findings.append(Diagnostic(finding_id, "error", f"Setup {field}: {status}; inspect and retry manually"))
                    elif status != "complete":
                        findings.append(Diagnostic(finding_id, "unknown", f"Setup {field}: {status}"))
        except (OSError, ValueError, AttributeError) as error:
            findings.append(Diagnostic("selection", "error", f"Invalid saved installation selection: {error}"))
        profile = None
        if selected:
            try:
                profile = SoftwareProfileResolver(self.applications.specs).resolve(selected, optional_packages=optional)
                desired = profile.get_packages()
            except ValueError as error:
                findings.append(Diagnostic("profiles", "error", f"Invalid selected profiles: {error}"))
        elif optional:
            desired = list(dict.fromkeys(optional))
        active_profiles = set(profile.selected_profiles) if profile else set()
        active_specs = [spec for spec in self.applications.specs if set(spec.profiles) & active_profiles
                        or set(spec.packages) & set(desired)]
        install = ["install"]
        for profile_name in selected:
            install.extend(("--profile", profile_name))
        for package in optional:
            install.extend(("--package", package))
        try:
            installed = self.inventory()
            for package in desired:
                missing = package not in installed
                findings.append(Diagnostic("package:" + package, "error" if missing else "ok",
                    ("Missing selected package: " if missing else "Installed package: ") + package,
                    tuple(install) if missing else (), privileged=missing))
        except (OSError, RuntimeError) as error:
            findings.append(Diagnostic("packages", "unknown", f"Cannot inspect package inventory: {error}"))
        self._outputs(findings, active_specs)
        if "desktop" in active_profiles:
            try:
                self._links(findings)
            except OSError as error:
                findings.append(Diagnostic("links", "unknown", f"Cannot inspect all Stow links: {error}"))
        self._permissions(findings)
        if wayland and not dry_run and "desktop" in active_profiles:
            external_agent = os.environ.get("SSH_AUTH_SOCK", "")
            units = [spec.user_unit for spec in active_specs if spec.user_unit
                     and not (spec.id == "ssh-agent" and external_agent and not external_agent.endswith("/shade-raid-ssh/agent.socket"))]
            for unit in [*units, "xdg-desktop-portal.service"]:
                try:
                    result = self.query(["systemctl", "--user", "is-active", unit])
                except OSError as error:
                    findings.append(Diagnostic("service:" + unit, "unknown", f"Cannot inspect {unit}: {error}"))
                    continue
                active = result.returncode == 0 and result.stdout.strip() == "active"
                unknown = result.returncode not in {0, 1, 3} or (not active and result.stdout.strip() != "failed")
                portal_unverified = active and unit == "xdg-desktop-portal.service"
                findings.append(Diagnostic("service:" + unit, "unknown" if unknown or portal_unverified else "ok" if active else "error",
                    (f"{unit}: frontend active; backend and interface health not verified" if portal_unverified else
                     f"{unit}: {result.stdout.strip() or result.stderr.strip() or 'status unavailable'}"),
                    (),
                    evidence=str(result.returncode)))
        elif dry_run:
            findings.append(Diagnostic("services", "unknown", "Service queries deferred in dry-run"))
        if dry_run:
            findings.append(Diagnostic("git", "unknown", "Git query deferred in dry-run"))
        else:
            try:
                result = self.query(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(self.env.dotfiles_dir),
                                     "status", "--porcelain", "--untracked-files=no"])
            except OSError as error:
                findings.append(Diagnostic("git", "unknown", f"Git status unavailable: {error}"))
            else:
                severity = "unknown" if result.returncode else "warning" if result.stdout.strip() else "ok"
                findings.append(Diagnostic("git", severity, "Git status unavailable" if result.returncode else
                                          "Git working tree has tracked changes" if result.stdout.strip() else "Git tracked working tree clean; untracked files not checked",
                                          evidence=result.stdout))
        outputs = tuple(item.message for item in findings if item.id.startswith("output:"))
        units = tuple(spec.user_unit for spec in active_specs if spec.user_unit)
        effects = {
            "configure": (*outputs,
                f"May create transaction journals and backups under {self.env.state_dir / 'transactions'}",
                f"May update {self.env.state_dir / 'active-theme'} and {self.env.preview_file}",
                f"May append command logs to {self.env.state_dir / 'commands.jsonl'} and use {self.env.lock_dir}",
                "May run Sass and refresh affected desktop applications; does not change wallpaper"),
            "link": (f"May create or migrate Stow links under {self.env.home_dir}",
                     f"May create migration backups under {self.env.home_dir / '.shade-raid-backups'}"),
            "session": ("Imports session environment and may start user units: " + ", ".join(units),
                        "May start xdg-desktop-portal.service"),
            "portal": ("Imports session environment and may start xdg-desktop-portal.service",),
        }
        return DiagnosticReport(tuple(findings), effects)

    def _outputs(self, findings, active_specs):
        active_ids = {spec.id for spec in active_specs}
        generators = [generator for generator in self.planner.generators if generator.name in active_ids]
        if not generators:
            return
        try:
            name = self.theme_store.get_active_theme()
            planner = ThemePlanner(self.env, self.planner.store, generators, self.applications)
            def artifact_error(artifact, error):
                findings.append(Diagnostic("output:" + artifact.artifact_id, "error",
                    f"Cannot inspect output {artifact.artifact_id}: {error}"))
            plan = planner.build(ThemeLoader(self.env).load(name), name, on_artifact_error=artifact_error)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            findings.append(Diagnostic("theme", "error", f"Cannot validate theme plan: {error}"))
            return
        for item in plan.artifacts:
            evidence = hashlib.sha256((item.original or b"") + item.artifact.content.encode()).hexdigest() + str(item.original_link)
            severity = "error" if item.original is None else "warning" if item.changed else "ok"
            message = ("Missing output: " if item.original is None else "Outdated output: " if item.changed else "Current output: ") + str(item.path)
            try:
                if item.original is not None:
                    ArtifactValidator().validate(item.path, item.original.decode("utf-8"))
            except (ValueError, UnicodeError) as error:
                severity, message = "error", f"Invalid output {item.path}: {error}"
            findings.append(Diagnostic("output:" + item.artifact.artifact_id, severity, message,
                                      ("configure", "--theme", name) if severity != "ok" else (), evidence=evidence))
        from dotfiles_api.infrastructure.theme_styler import ThemeStyler
        rendered = {item.artifact.artifact_id: item for item in plan.artifacts}
        for spec in active_specs:
            for style in spec.stylesheets:
                try:
                    path = self.planner.store.resolve_path(style.output, name)
                    self.env.validate_output_path(path)
                    expected = ThemeStyler.source_digest(self.env, style, rendered)
                    raw = read_regular_file(path)
                    content = raw.decode("utf-8") if raw is not None else ""
                    ArtifactValidator().validate(path, content)
                    parts = content.split("\n", 2)
                    current = (len(parts) == 3 and parts[0] == f"/* shade-raid-source: {expected} */"
                               and parts[1] == f"/* shade-raid-content: {hashlib.sha256(parts[2].encode()).hexdigest()} */")
                    findings.append(Diagnostic("output:" + style.output, "ok" if current else "error",
                        f"{'Current' if current else 'Missing/outdated'} compiled stylesheet: {path}",
                        () if current else ("configure", "--theme", name), evidence=hashlib.sha256(content.encode()).hexdigest() + expected))
                except (OSError, ValueError, KeyError) as error:
                    findings.append(Diagnostic("output:" + style.output, "error", f"Stylesheet validation failed: {error}",
                                              ("configure", "--theme", name)))

    def _links(self, findings):
        for source in sorted(self.env.source_home.rglob("*")):
            try:
                if source.is_dir():
                    continue
                target = self.env.home_dir / source.relative_to(self.env.source_home)
                if target.is_symlink() and target.resolve() == source.resolve() and source.exists():
                    continue
                missing = not target.exists()
                findings.append(Diagnostic("link:" + str(target), "error" if missing else "warning",
                    ("Missing Stow link: " if missing else "Personal/other source overrides Stow: ") + str(target),
                    ("link",) if missing else (), evidence=str(source.stat().st_mtime_ns) + str(target.readlink() if target.is_symlink() else "")))
            except (OSError, ValueError) as error:
                findings.append(Diagnostic("link:" + str(source), "unknown", f"Cannot inspect Stow entry {source}: {error}"))

    def _permissions(self, findings):
        seen = set()
        def inspect(path):
            if path in seen:
                return False
            seen.add(path)
            try:
                info = path.lstat()
            except FileNotFoundError:
                return False
            except OSError as error:
                findings.append(Diagnostic("permissions:" + str(path), "unknown", f"Cannot inspect private path {path}: {error}"))
                return False
            if stat.S_ISLNK(info.st_mode):
                findings.append(Diagnostic("permissions:" + str(path), "error", f"Private state path is a symlink: {path}", evidence="symlink"))
                return False
            directory = stat.S_ISDIR(info.st_mode)
            if not directory and not stat.S_ISREG(info.st_mode):
                findings.append(Diagnostic("permissions:" + str(path), "error", f"Private state path is not a regular file: {path}", evidence=str(info.st_mode)))
                return False
            if info.st_mode & 0o077:
                findings.append(Diagnostic("permissions:" + str(path), "error", f"Private state has broad permissions: {path}",
                                           ("chmod", "700" if directory else "600", str(path)), evidence=oct(info.st_mode & 0o777)))
            return directory

        state = self.env.state_dir
        inspect(state)
        for name in ("commands.jsonl", "installation.json", "active-theme", "preview-theme"):
            inspect(state / name)
        for root in (state / "transactions", self.env.runtime_dir):
            if not inspect(root):
                continue
            def onerror(error):
                findings.append(Diagnostic("permissions:" + str(error.filename), "unknown", f"Cannot inspect private path: {error}"))
            for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
                for name in list(dirs):
                    if not inspect(Path(directory) / name):
                        dirs.remove(name)
                for name in files:
                    inspect(Path(directory) / name)
        login_files = ("config.toml", "regreet.toml", "regreet.css", "hyprland-greet.conf", "regreet-background.jpg")
        installation_detected = any(os.path.lexists(self.login_dir / name) for name in login_files[1:])
        for name in login_files:
            path = self.login_dir / name
            try:
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                    findings.append(Diagnostic("login:" + name, "error", f"Insecure login configuration: {path}",
                                              ("setup-login",), privileged=True, evidence=str(info.st_mode)))
            except FileNotFoundError:
                if installation_detected and name in {"config.toml", "regreet.toml", "regreet.css", "hyprland-greet.conf", "regreet-background.jpg"}:
                    findings.append(Diagnostic("login:" + name, "error", f"Incomplete login installation, missing: {path}",
                                              ("setup-login",), privileged=True))
            except OSError as error:
                findings.append(Diagnostic("login:" + name, "unknown", f"Cannot inspect login permissions: {error}"))
        for name in ("shade-raid", "plymouth_sync", "regreet-theme"):
            path = self.login_dir.parent / "sudoers.d" / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            except OSError as error:
                findings.append(Diagnostic("sudoers:" + name, "unknown", f"Cannot inspect legacy sudoers path {path}: {error}", privileged=True))
                continue
            findings.append(Diagnostic("sudoers:" + name, "error", f"Legacy sudoers entry requires manual review: {path}",
                                       privileged=True, evidence=str(info.st_mode)))
