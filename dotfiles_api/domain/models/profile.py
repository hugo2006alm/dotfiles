from dataclasses import dataclass
from dotfiles_api.domain.models.feature import Feature

@dataclass(frozen=True)
class Profile:
    name: str
    features: list[Feature]

    def get_packages(self) -> list[str]:
        seen = set()
        result = []
        for feature in self.features:
            for package in feature.packages:
                if package not in seen:
                    seen.add(package)
                    result.append(package)
        return result
