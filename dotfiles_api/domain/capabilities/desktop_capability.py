from typing import Protocol

class DesktopCapability(Protocol):
    def get_capability_id(self) -> str:
        ...
