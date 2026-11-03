import shutil
from dotfiles_api.domain.contracts.action import Action


class ControlAction(Action):
    def __init__(self, execution, kind, direction):
        self.execution, self.kind, self.direction = execution, kind, direction

    def execute(self, args):
        if args:
            raise ValueError("Volume and brightness actions take no arguments")
        if shutil.which("swayosd-client"):
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
