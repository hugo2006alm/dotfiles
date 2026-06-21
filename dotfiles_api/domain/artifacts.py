from dataclasses import dataclass

@dataclass(frozen=True)
class GeneratedArtifact:
    artifact_id: str
    content: str
