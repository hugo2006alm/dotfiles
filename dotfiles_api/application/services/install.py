import json
import stat
from dotfiles_api.application.installation_planner import InstallationPlanner
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.package_inventory import PackageInventory
from dotfiles_api.application.installation_error import InstallationError


class InstallService:
    def __init__(self, env, exec_ctx, registry, sources, inventory=None):
        self._env, self._exec, self._registry, self._sources = env, exec_ctx, registry, sources
        self._planner = InstallationPlanner(registry, sources, inventory or PackageInventory().names)

    def install_profile(self, profile, *, setup=False):
        dry_run = bool(self._exec and self._exec.dry_run)
        previous, path = {}, None
        if self._env and not dry_run:
            path = self._env.state_dir / "installation.json"
            self._env.validate_output_path(path)
            if path.exists() or path.is_symlink():
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError(f"Unsafe installation state file: {path}")
                previous = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(previous, dict):
                    raise ValueError("Invalid installation state: expected an object")
                if previous.get("version", 1) not in (1, 2):
                    raise ValueError("Unsupported installation selection version")
                for key in ("profiles", "packages", "optional_packages", "requested_profiles", "explicit_packages"):
                    if not isinstance(previous.get(key, []), list) or not all(isinstance(v, str) for v in previous.get(key, [])):
                        raise ValueError(f"Invalid installation selection: {key}")
        plan = self._planner.build(profile, dry_run=dry_run)
        plan.describe(deferred=dry_run)
        if dry_run:
            print("No changes applied.")
            return plan
        # Record setup start after successful preflight and before external effects.
        # A process killed mid-install remains visibly in_progress on next run.
        if path and setup:
            started = dict(previous)
            started.setdefault("version", 1)
            started["package_status"] = "in_progress"
            started["desktop_configuration_status"] = "in_progress"
            started.setdefault("session_status", "not_checked")
            SystemFileWriter().write(path, json.dumps(started, indent=2) + "\n")
        completed = []
        try:
            for source_id, packages in plan.groups:
                try:
                    self._sources[source_id].install(list(packages))
                except Exception as error:
                    raise InstallationError(tuple(completed), source_id) from error
                completed.append((source_id, tuple(packages)))
        except BaseException:
            if path and setup:
                try:
                    started["package_status"] = "failed_or_partial"
                    started["desktop_configuration_status"] = "failed"
                    SystemFileWriter().write(path, json.dumps(started, indent=2) + "\n")
                except Exception as error:
                    import sys
                    print(f"Could not record interrupted setup: {error}", file=sys.stderr)
            raise
        if path:
            # Version 1 stored resolved historical packages as if they were choices.
            # Only profile choices and explicitly selected extras are durable intent.
            requested = previous.get("requested_profiles", previous.get("profiles", []))
            explicit = previous.get("explicit_packages", previous.get("optional_packages", []))
            requested = list(dict.fromkeys([*requested, *(profile.requested_profiles or profile.selected_profiles)]))
            explicit = list(dict.fromkeys([*explicit, *profile.optional_packages]))
            selection = {"version": 2, "requested_profiles": requested, "explicit_packages": explicit,
                         "profiles": requested, "optional_packages": explicit,
                         "packages": profile.get_packages(), "package_status": "complete",
                         "desktop_configuration_status": "in_progress" if setup else previous.get("desktop_configuration_status", "not_recorded"),
                         "session_status": previous.get("session_status", "not_checked")}
            SystemFileWriter().write(path, json.dumps(selection, indent=2) + "\n")
        return plan

    def record_setup_status(self, status):
        if status not in {"in_progress", "failed", "complete"}:
            raise ValueError(f"Invalid setup status: {status}")
        if not self._env or (self._exec and self._exec.dry_run):
            return
        path = self._env.state_dir / "installation.json"
        self._env.validate_output_path(path)
        if not path.exists() and not path.is_symlink():
            raise RuntimeError("Package installation status missing; cannot record setup")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError(f"Unsafe installation state file: {path}")
        state = json.loads(path.read_text(encoding="utf-8"))
        state["desktop_configuration_status"] = status
        SystemFileWriter().write(path, json.dumps(state, indent=2) + "\n")
