from dotfiles_api.domain.contracts.action import Action


class MediaAction(Action):
    def __init__(self, execution, command):
        self.execution, self.command = execution, command

    def execute(self, args):
        if args:
            raise ValueError("Media actions take no arguments")
        if self.execution.dry_run:
            print(f"[DRY-RUN] Would select the playing MPRIS player and {self.command}")
            return
        listing = self.execution.optional(["playerctl", "-l"], step="media:list")
        players = listing.stdout.splitlines() if listing.returncode == 0 else []
        candidates = []
        for player in players:
            status = self.execution.optional(["playerctl", "--player", player, "status"], step="media:status")
            if status.returncode == 0:
                candidates.append((status.stdout.strip() != "Playing", player))
        if not candidates:
            self.execution.optional(["notify-send", "Shade Raid", "No media player available"])
            return
        player = min(candidates, key=lambda candidate: candidate[0])[1]
        self.execution.execute(["playerctl", "--player", player, self.command], step="media:control")
