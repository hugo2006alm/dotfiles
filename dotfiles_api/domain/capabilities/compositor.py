from typing import Protocol
from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class Compositor(DesktopCapability, Protocol):
    def reload_compositor(self) -> None:
        ...
