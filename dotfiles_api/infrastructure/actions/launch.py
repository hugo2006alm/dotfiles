import shutil
from dotfiles_api.domain.contracts.action import Action


class LaunchAction(Action):
    def __init__(self, execution, applications):
        self.execution = execution
        self.applications = {spec.id: spec for spec in applications}

    def execute(self, args):
        if not args or args[0] not in self.applications or not self.applications[args[0]].launch:
            raise ValueError("Specify an application ID with a launch command")
        spec = self.applications[args[0]]
        if not self.execution.dry_run and not shutil.which(spec.launch[0]):
            requirement = ", ".join(spec.packages)
            self.execution.optional(["notify-send", "Application unavailable", f"{spec.id}: install {requirement}"])
            raise RuntimeError(f"{spec.id} requires {requirement}")
        self.execution.spawn([*spec.launch, *args[1:]], step=f"launch:{spec.id}", sensitive=True)
