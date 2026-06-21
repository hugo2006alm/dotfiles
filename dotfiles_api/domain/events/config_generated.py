from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigGeneratedEvent:
    generator_name: str
