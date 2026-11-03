import json
from dotfiles_api.application.installation_planner import InstallationPlanner
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.package_inventory import PackageInventory


class InstallService:
    def __init__(self, env, exec_ctx, registry, sources, inventory=None):
        self._env, self._exec, self._registry, self._sources = env, exec_ctx, registry, sources
        self._planner = InstallationPlanner(registry, sources, inventory or PackageInventory().names)

    def install_profile(self, profile):
        dry_run = bool(self._exec and self._exec.dry_run)
        previous, path = {}, None
        if self._env and not dry_run:
            path = self._env.state_dir / "installation.json"
            self._env.validate_output_path(path)
            if path.exists():
                previous = json.loads(path.read_text(encoding="utf-8"))
                for key in ("profiles", "packages", "optional_packages"):
                    if not isinstance(previous.get(key, []), list) or not all(isinstance(v, str) for v in previous.get(key, [])):
                        raise ValueError(f"Invalid installation selection: {key}")
        plan = self._planner.build(profile, dry_run=dry_run)
        plan.describe(deferred=dry_run)
        if dry_run:
            print("No changes applied.")
            return plan
        for source_id, packages in plan.groups:
            self._sources[source_id].install(list(packages))
        if path:
            selection = {"version": 1}
            for key, values in (("profiles", profile.selected_profiles), ("packages", profile.get_packages()),
                                ("optional_packages", profile.optional_packages)):
                selection[key] = list(dict.fromkeys([*previous.get(key, []), *values]))
            SystemFileWriter().write(path, json.dumps(selection, indent=2) + "\n")
        return plan
