import hashlib
import json
import os
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
        selected, optional, desired = ["desktop"], [], None
        selection = self.env.state_dir / "installation.json"
        if selection.exists():
            try:
                data = json.loads(selection.read_text())
                for key in ("profiles", "packages", "optional_packages"):
                    if not isinstance(data.get(key, []), list) or not all(isinstance(value, str) for value in data.get(key, [])):
                        raise ValueError(f"invalid {key}")
                selected, optional, desired = data.get("profiles") or selected, data.get("optional_packages", []), data.get("packages", [])
            except (OSError, ValueError, AttributeError) as error:
                findings.append(Diagnostic("selection", "error", f"Invalid saved installation selection: {error}"))
        try:
            profile = SoftwareProfileResolver(self.applications.specs).resolve(selected)
        except ValueError as error:
            findings.append(Diagnostic("profiles", "error", f"Invalid selected profiles: {error}"))
            profile = SoftwareProfileResolver(self.applications.specs).resolve(["desktop"])
        if desired is None:
            desired = profile.get_packages()
        active_specs = [spec for spec in self.applications.specs if set(spec.profiles) & set(profile.selected_profiles)
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
        except OSError as error:
            findings.append(Diagnostic("packages", "unknown", f"Cannot inspect package inventory: {error}"))
        self._outputs(findings, active_specs)
        if "desktop" in profile.selected_profiles:
            try:
                self._links(findings)
            except OSError as error:
                findings.append(Diagnostic("links", "unknown", f"Cannot inspect all Stow links: {error}"))
        self._permissions(findings)
        if wayland and not dry_run and "desktop" in profile.selected_profiles:
            external_agent = os.environ.get("SSH_AUTH_SOCK", "")
            units = [spec.user_unit for spec in active_specs if spec.user_unit
                     and not (spec.id == "ssh-agent" and external_agent and not external_agent.endswith("/shade-raid-ssh/agent.socket"))]
            for unit in [*units, "xdg-desktop-portal.service"]:
                result = self.query(["systemctl", "--user", "is-active", unit])
                active = result.returncode == 0 and result.stdout.strip() == "active"
                unknown = result.returncode not in {0, 1, 3}
                findings.append(Diagnostic("service:" + unit, "unknown" if unknown else "ok" if active else "error",
                    f"{unit}: {result.stdout.strip() or result.stderr.strip() or 'status unavailable'}",
                    () if active or unknown else ("portal",) if unit.startswith("xdg-desktop-portal") else ("session",),
                    evidence=str(result.returncode)))
        elif dry_run:
            findings.append(Diagnostic("services", "unknown", "Service queries deferred in dry-run"))
        if dry_run:
            findings.append(Diagnostic("git", "unknown", "Git query deferred in dry-run"))
        else:
            result = self.query(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(self.env.dotfiles_dir),
                                 "status", "--porcelain", "--untracked-files=no"])
            severity = "unknown" if result.returncode else "warning" if result.stdout.strip() else "ok"
            findings.append(Diagnostic("git", severity, "Git status unavailable" if result.returncode else
                                      "Git working tree has tracked changes" if result.stdout.strip() else "Git working tree clean",
                                      evidence=result.stdout))
        return DiagnosticReport(tuple(findings))

    def _outputs(self, findings, active_specs):
        active_ids = {spec.id for spec in active_specs}
        generators = [generator for generator in self.planner.generators if generator.name in active_ids]
        if not generators:
            return
        try:
            name = self.theme_store.get_active_theme()
            planner = ThemePlanner(self.env, self.planner.store, generators, self.applications)
            plan = planner.build(ThemeLoader(self.env).load(name), name)
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
                except (OSError, ValueError) as error:
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
        for name in ("commands.jsonl", "installation.json", "active-theme"):
            path = self.env.state_dir / name
            if path.exists() and path.stat().st_mode & 0o077:
                findings.append(Diagnostic("permissions:" + name, "error", f"Private state has broad permissions: {path}",
                                          ("chmod", "600", str(path)), evidence=oct(path.stat().st_mode & 0o777)))
        for name in ("config.toml", "regreet.toml", "regreet.css", "hyprland-greet.conf"):
            path = self.login_dir / name
            try:
                if path.exists() and (path.is_symlink() or path.stat().st_uid != 0 or path.stat().st_mode & 0o022):
                    findings.append(Diagnostic("login:" + name, "error", f"Insecure login configuration: {path}",
                                              ("setup-login",), privileged=True, evidence=str(path.stat().st_mode)))
            except OSError as error:
                findings.append(Diagnostic("login:" + name, "unknown", f"Cannot inspect login permissions: {error}"))
