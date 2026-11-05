from pathlib import Path
import re
import shutil

from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.domain.models.application_spec import ApplicationSpec


class ApplicationRegistry:
    def __init__(self, specs: tuple[ApplicationSpec, ...], source_overrides=None) -> None:
        self.specs = specs
        self._source_overrides = dict(source_overrides or {})
        self._by_id = {spec.id: spec for spec in specs}
        if len(self._by_id) != len(specs):
            raise ValueError("Duplicate application IDs")
        visited, visiting, output_ids, paths, units = set(), set(), set(), set(), set()

        def visit(name):
            if name not in self._by_id:
                raise ValueError(f"Unknown application dependency: {name}")
            if name in visiting:
                raise ValueError(f"Application dependency cycle: {name}")
            if name in visited:
                return
            visiting.add(name)
            for dependency in self._by_id[name].dependencies:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        units = set()
        for spec in specs:
            visit(spec.id)
            for dependency in spec.runtime_dependencies:
                if dependency not in self._by_id:
                    raise ValueError(f"Unknown runtime dependency: {dependency}")
            if spec.reload_strategy not in {"none", "application", "systemd-user-reload", "systemd-user-restart"}:
                raise ValueError(f"Invalid reload strategy: {spec.id}")
            if spec.reload_strategy == "none" and spec.reload_factory:
                raise ValueError(f"Reload factory requires a strategy: {spec.id}")
            if spec.reload_strategy == "application" and not spec.reload_factory:
                raise ValueError(f"Application reload requires a factory: {spec.id}")
            if spec.reload_strategy.startswith("systemd-user-") and not spec.user_unit:
                raise ValueError(f"Systemd reload requires a user unit: {spec.id}")
            if spec.user_unit:
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.service", spec.user_unit) or spec.user_unit in units:
                    raise ValueError(f"Invalid or duplicate user unit: {spec.user_unit}")
                units.add(spec.user_unit)
            for executable in spec.runtime_executables:
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", executable):
                    raise ValueError(f"Invalid executable for {spec.id}: {executable}")
            for output in spec.outputs:
                path = Path(output.path)
                if path.is_absolute() or ".." in path.parts or output.scope not in {"home", "state"}:
                    raise ValueError(f"Unsafe application output: {output}")
                if output.id in output_ids or (output.scope, path) in paths:
                    raise ValueError(f"Duplicate application output: {output}")
                output_ids.add(output.id)
                paths.add((output.scope, path))
            declared = {output.id for output in spec.outputs}
            compiled = set()
            for style in spec.stylesheets:
                if (Path(style.source).is_absolute() or ".." in Path(style.source).parts
                        or style.output not in declared or not set(style.inputs) <= declared
                        or style.output in compiled or style.output in style.inputs):
                    raise ValueError(f"Invalid stylesheet contract in {spec.id}: {style}")
                mapped, targets = set(), set()
                for artifact_id, relative in style.input_paths:
                    path = Path(relative)
                    if (artifact_id not in style.inputs or artifact_id in mapped or path.is_absolute()
                            or not path.parts or ".." in path.parts or path == Path(Path(style.source).name)
                            or path in targets):
                        raise ValueError(f"Invalid stylesheet input mapping in {spec.id}: {artifact_id}, {relative}")
                    mapped.add(artifact_id)
                    targets.add(path)
                compiled.add(style.output)
        self.package_sources()

    def artifact_paths(self, env, validate=True):
        paths = {"active-theme": env.state_dir / "active-theme", "theme-preview": env.preview_file}
        for spec in self.specs:
            for output in spec.outputs:
                if output.id in paths:
                    raise ValueError(f"Reserved output ID: {output.id}")
                target = (env.home_dir if output.scope == "home" else env.state_dir) / output.path
                if validate:
                    env.validate_output_path(target)
                paths[output.id] = target
        return paths

    def generators(self, transaction, event_bus):
        return [spec.generator(name=spec.id, transaction=transaction, event_bus=event_bus)
                for spec in self.specs if spec.generator]

    def reloadables(self, execution, env, theme_store, loader):
        return [spec.reload_factory(execution, env, theme_store, loader)
                for spec in self.specs if spec.reload_factory and
                (spec.required or not spec.runtime_executables or
                 any(shutil.which(name) for name in spec.runtime_executables))]

    def installation_specs(self, profiles, selected_packages=(), include_profile_optional=False):
        """Return selected applications and their installation dependencies."""
        selected = set(selected_packages)
        seeds = [spec.id for spec in self.specs
                 if ((spec.required or include_profile_optional) and set(spec.profiles).intersection(profiles))
                 or (selected and selected.intersection(spec.packages))]
        ordered, seen = [], set()
        def visit(name):
            if name in seen:
                return
            seen.add(name)
            spec = self._by_id[name]
            for dependency in spec.dependencies:
                visit(dependency)
            ordered.append(spec)
        for name in seeds:
            visit(name)
        return ordered

    def packages(self, profile):
        return list(dict.fromkeys(package for spec in self.installation_specs([profile]) for package in spec.packages))

    def package_sources(self):
        declared = {}
        known = {package for spec in self.specs for package in spec.packages}
        for package, source in self._source_overrides.items():
            if package not in known or source not in {"pacman", "yay"}:
                raise ValueError(f"Invalid package source override: {package}, {source}")
        for spec in self.specs:
            overrides = {}
            for package, source in spec.package_sources:
                if package not in spec.packages or source not in {"pacman", "yay"} or package in overrides:
                    raise ValueError(f"Invalid package source in {spec.id}: {package}, {source}")
                overrides[package] = source
            for package in spec.packages:
                source = overrides.get(package, "pacman")
                if package in declared and declared[package] != source and package not in self._source_overrides:
                    raise ValueError(f"Conflicting package sources for {package}: {declared[package]}, {source}")
                declared[package] = self._source_overrides.get(package, source)
        return declared

    def validate_artifacts(self, name, artifacts):
        spec = self._by_id[name]
        compiled = {style.output for style in spec.stylesheets}
        expected = {output.id for output in spec.outputs} - compiled
        actual = [artifact.artifact_id for artifact in artifacts]
        if set(actual) != expected or len(actual) != len(expected):
            raise ValueError(f"Application {name} outputs differ: expected {sorted(expected)}, got {actual}")

    def validate_outputs(self, generators, tokens, theme_name):
        for generator in generators:
            self.validate_artifacts(generator.name, generator.render(tokens, theme_name))

    def validate_content(self, name, path, content):
        validator = self._by_id[name].validator or ArtifactValidator().validate
        validator(path, content)
