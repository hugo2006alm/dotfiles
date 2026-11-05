from dotfiles_api.domain.contracts.action import Action


class SessionAction(Action):
    def __init__(self, session, env=None, reloads=None, wallpaper=None, dry_run=False):
        self.session, self.env, self.reloads, self.wallpaper = session, env, reloads, wallpaper
        self.dry_run = dry_run

    def execute(self, args):
        if args:
            raise ValueError("Session action takes no arguments")
        self.session.start()
        if self.dry_run or self.env is None or self.reloads is None:
            return
        pending = self.env.state_dir / "pending-refresh"
        self.env.validate_output_path(pending)
        if pending.is_symlink() or (pending.exists() and not pending.is_file()):
            raise ValueError(f"Unsafe pending refresh marker: {pending}")
        if pending.is_file():
            if self.wallpaper is not None:
                self.wallpaper.execute([])
            self.reloads.reload_all()
