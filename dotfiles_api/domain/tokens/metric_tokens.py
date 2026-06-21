from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MetricTokens:
    metrics: dict[str, Any]
