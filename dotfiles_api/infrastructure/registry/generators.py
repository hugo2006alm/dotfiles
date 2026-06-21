from dotfiles_api.infrastructure.generators.base import BaseGenerator

class GeneratorRegistry:
    def __init__(self) -> None:
        self._generators: dict[str, BaseGenerator] = {}

    def register(self, name: str, generator: BaseGenerator) -> None:
        self._generators[name] = generator

    def get_all(self) -> list[BaseGenerator]:
        return list(self._generators.values())
