from dataclasses import asdict, dataclass
from dotfiles_api.domain.models.diagnostic import Diagnostic


@dataclass(frozen=True)
class DiagnosticReport:
    findings: tuple[Diagnostic, ...]

    @property
    def exit_code(self):
        return int(any(item.severity == "error" for item in self.findings))

    def to_dict(self):
        return {"version": 1, "exit_code": self.exit_code, "findings": [asdict(item) for item in self.findings]}

    def describe(self):
        print("Shade Raid Doctor")
        for item in self.findings:
            if item.severity != "ok":
                print(f"  [{item.severity}] {item.message}")
        issues = sum(item.severity in {"warning", "error"} for item in self.findings)
        unknown = sum(item.severity == "unknown" for item in self.findings)
        print(f"{issues} issues; {unknown} checks unknown/deferred. Run dotfiles repair --plan to review fixes.")
