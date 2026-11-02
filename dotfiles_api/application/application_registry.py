from pathlib import Path

from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.domain.models.application_spec import ApplicationSpec


class ApplicationRegistry:
    def __init__(self, specs: tuple[ApplicationSpec, ...]) -> None:
        self.specs = specs
        self._by_id = {spec.id: spec for spec in specs}
        if len(self._by_id) != len(specs):
            raise ValueError("Duplicate application IDs")
        visited, visiting, output_ids, paths = set(), set(), set(), set()

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

        for spec in specs:
            visit(spec.id)
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
                compiled.add(style.output)

    def artifact_paths(self, env):
        paths = {"active-theme": env.state_dir / "active-theme", "theme-preview": env.preview_file}
        for spec in self.specs:
            for output in spec.outputs:
                if output.id in paths:
                    raise ValueError(f"Reserved output ID: {output.id}")
                target = (env.home_dir if output.scope == "home" else env.state_dir) / output.path
                env.validate_output_path(target)
                paths[output.id] = target
        return paths

    def generators(self, transaction, event_bus):
        return [spec.generator(name=spec.id, transaction=transaction, event_bus=event_bus)
                for spec in self.specs if spec.generator]

    def reloadables(self, execution, env, theme_store, loader):
        return [spec.reload_factory(execution, env, theme_store, loader)
                for spec in self.specs if spec.reload_factory]

    def packages(self, profile):
        return list(dict.fromkeys(package for spec in self.specs if spec.required and profile in spec.profiles
                                  for package in spec.packages))

    def package_sources(self):
        sources = {package: "pacman" for spec in self.specs for package in spec.packages}
        for spec in self.specs:
            for package, source in spec.package_sources:
                if package not in spec.packages or source not in {"pacman", "yay"}:
                    raise ValueError(f"Invalid package source in {spec.id}: {package}, {source}")
                sources[package] = source
        return sources

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
