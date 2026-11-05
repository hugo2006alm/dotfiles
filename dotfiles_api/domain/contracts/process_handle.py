from typing import Protocol


class ProcessHandle(Protocol):
    """Caller-owned child lifecycle; spawn does not promise application readiness."""

    pid: int

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...
