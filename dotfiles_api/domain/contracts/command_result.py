from dataclasses import dataclass

@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int
