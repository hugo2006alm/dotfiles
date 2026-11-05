import shutil
from dotfiles_api.domain.contracts.action import Action


class ControlAction(Action):
    def __init__(self, execution, kind, direction):
        self.execution, self.kind, self.direction = execution, kind, direction

    def execute(self, args):
        if args:
            raise ValueError("Volume and brightness actions take no arguments")
        osd_active = False
        if shutil.which("swayosd-client"):
            status = self.execution.query(["systemctl", "--user", "is-active", "--quiet", "shade-raid-swayosd.service"],
                                          allowed_returncodes=(0, 1, 3, 4, 127), step="control:osd-status")
            osd_active = status.returncode == 0
        if osd_active:
            flag = "--output-volume" if self.kind == "volume" else "--brightness"
            value = {"up": "raise", "down": "lower", "mute": "mute-toggle"}[self.direction]
            command = ["swayosd-client", flag, value]
        elif self.kind == "brightness":
            command = ["brightnessctl", "set", "5%+" if self.direction == "up" else "5%-"]
        elif self.direction == "mute":
            command = ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]
        else:
            command = ["wpctl", "set-volume", "--limit", "1.0", "@DEFAULT_AUDIO_SINK@",
                       "5%+" if self.direction == "up" else "5%-"]
        self.execution.execute(command, step=f"control:{self.kind}")
