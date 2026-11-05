class InstallationError(RuntimeError):
    """Installation commands may have effects which cannot be compensated."""

    def __init__(self, completed_groups: tuple[tuple[str, tuple[str, ...]], ...],
                 failed_source: str) -> None:
        self.completed_groups = completed_groups
        self.failed_source = failed_source
        completed = "; ".join(f"{source}: {', '.join(packages)}" for source, packages in completed_groups)
        super().__init__(
            f"Installation failed in {failed_source}; completed group commands: {completed or 'none'}. "
            "The failed group may have partial effects. Package changes were not rolled back; "
            "inspect installed inventory before retrying."
        )
