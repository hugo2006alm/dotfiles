from dataclasses import dataclass
import hashlib
import json
import shlex
from dotfiles_api.domain.models.diagnostic_report import DiagnosticReport


@dataclass(frozen=True)
class RepairPlan:
    report: DiagnosticReport

    @property
    def id(self):
        return hashlib.sha256(json.dumps(self.report.to_dict(), sort_keys=True).encode()).hexdigest()

    @property
    def operations(self):
        operations, seen = [], set()
        for item in self.report.findings:
            if item.repair and item.repair not in seen:
                seen.add(item.repair)
                operations.append(item)
        order = {"link": 0, "configure": 1, "session": 2, "portal": 3}
        return tuple(sorted(operations, key=lambda item: order.get(item.repair[0], 4)))

    def describe(self):
        self.report.describe()
        print("REPAIR PLAN " + self.id)
        for item in self.operations:
            automatic = item.repair[0] in {"configure", "link", "session", "portal"} and not item.privileged
            command = ("dotfiles", "action", *item.repair) if item.repair[0] in {"session", "portal"} else ("dotfiles", *item.repair)
            if item.repair[0] == "chmod":
                command = item.repair
            print(f"  {'apply' if automatic else 'manual'}: {shlex.join(command)}")
            if automatic:
                for effect in self.report.effects.get(item.repair[0], ()):
                    print(f"    effect: {effect}")
        print(f"Review first, then: dotfiles repair --apply --plan-id {self.id}")
