from typing import Protocol
from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class StatusBar(DesktopCapability, Protocol):
    def toggle(self) -> None:
        ...
