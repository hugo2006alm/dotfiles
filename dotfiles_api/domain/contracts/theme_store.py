from typing import Protocol

class ThemeStore(Protocol):
    def get_active_theme(self) -> str:
        ...
    def set_active_theme(self, theme_name: str) -> None:
        ...
