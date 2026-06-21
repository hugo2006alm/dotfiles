from pathlib import Path

class ArtifactStore:
    def __init__(self, mappings: dict[str, Path]) -> None:
        self._mappings = mappings

    def resolve_path(self, artifact_id: str) -> Path:
        if artifact_id not in self._mappings:
            raise KeyError(f"Artifact ID '{artifact_id}' not found in registry.")
        return self._mappings[artifact_id]
