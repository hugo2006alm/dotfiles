from typing import Protocol

class DesktopCapability(Protocol):
    CAPABILITY_ID: str = ""

    def get_capability_id(self) -> str:
        return self.CAPABILITY_ID
