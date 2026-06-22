from typing import Protocol
from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class Launcher(DesktopCapability, Protocol):
    CAPABILITY_ID: str = "launcher"

    def launch(self) -> None:
        ...
