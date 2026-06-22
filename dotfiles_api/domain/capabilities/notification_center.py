from typing import Protocol
from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class NotificationCenter(DesktopCapability, Protocol):
    CAPABILITY_ID: str = "notification-center"

    def toggle_center(self) -> None:
        ...
