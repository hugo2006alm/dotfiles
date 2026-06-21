from dotfiles_api.domain.capabilities.desktop_capability import DesktopCapability

class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, DesktopCapability] = {}

    def register(self, name: str, capability: DesktopCapability) -> None:
        self._capabilities[name] = capability

    def get(self, name: str) -> DesktopCapability | None:
        return self._capabilities.get(name)

    def get_all(self) -> list[DesktopCapability]:
        return list(self._capabilities.values())
