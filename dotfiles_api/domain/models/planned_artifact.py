from dataclasses import dataclass
from pathlib import Path
from dotfiles_api.domain.artifacts import GeneratedArtifact


@dataclass(frozen=True)
class PlannedArtifact:
    generator: str
    artifact: GeneratedArtifact
    path: Path
    original: bytes | None

    @property
    def changed(self) -> bool:
        return self.original != self.artifact.content.encode("utf-8")
