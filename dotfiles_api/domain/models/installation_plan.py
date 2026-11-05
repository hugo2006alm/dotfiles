from dataclasses import dataclass


@dataclass(frozen=True)
class InstallationPlan:
    groups: tuple[tuple[str, tuple[str, ...]], ...]
    installed: tuple[str, ...]

    def describe(self, deferred=False):
        print("INSTALL PLAN")
        print(f"  Keep {len(self.installed)} already installed packages")
        for source, packages in self.groups:
            print(f"  {source}: {' '.join(packages)}")
        if deferred:
            print("  Availability checks deferred; no commands or network requests run in dry-run")
