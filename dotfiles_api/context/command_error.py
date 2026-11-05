class CommandExecutionError(RuntimeError):
    """A required command failed. All supplied diagnostic text is redacted."""

    def __init__(self, command: str, returncode: int, diagnostic: str, step: str) -> None:
        self.returncode = returncode
        self.step = step
        super().__init__(f"{step}: {command} failed (exit {returncode}): {diagnostic}")
