from dataclasses import dataclass
from dotfiles_api.domain.models.planned_artifact import PlannedArtifact


@dataclass(frozen=True)
class ThemePlan:
    theme_name: str
    artifacts: tuple[PlannedArtifact, ...]
    source_snapshot: tuple[tuple[str, bytes], ...] | None = None

    @property
    def changed_generators(self) -> frozenset[str]:
        return frozenset(item.generator for item in self.artifacts if item.changed)

    def describe(self) -> None:
        changed = sum(item.changed for item in self.artifacts)
        print(f"PLAN: theme {self.theme_name}")
        print(f"  Generate {len(self.artifacts)} artifacts")
        print(f"  Update {changed} files; keep {len(self.artifacts) - changed} unchanged")
        for item in self.artifacts:
            operation = "CREATE" if item.original is None else "UPDATE" if item.changed else "KEEP"
            print(f"  {operation} {item.path} [{item.generator}]")
        if self.changed_generators:
            print("  Refresh after commit: " + ", ".join(sorted(self.changed_generators)))
        print("  Runtime availability and application-level validation deferred until execution")
        print("  Skip privileged greetd installation (explicit setup-login required)")
