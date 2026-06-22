from typing import Protocol
from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class StatusBar(DesktopCapability, Protocol):
    CAPABILITY_ID: str = "status-bar"

    def toggle(self) -> None:
        ...
