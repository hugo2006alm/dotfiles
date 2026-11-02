# Installation and login recovery

## Before changing a desktop

Record the Git revision, `pacman -Q`, `systemctl is-enabled greetd`,
`systemctl status greetd`, and relevant configuration symlinks and permissions.
Keep a second TTY logged in; verify Ctrl+Alt+F3 and your account password work.
Test the changes in a disposable Arch VM before the main installation.

Normal setup, configure, toggle and reload do not install login files.
Run `dotfiles setup-login` yourself in an interactive terminal to opt in.
It enables greetd for subsequent boots without restarting the current session.
It validates TOML, stages files privately, creates a root-owned mode-0700
snapshot under `/var/backups/shade-raid/`, and prints its location before
replacing login files. Installed files are root:root mode 0644.
Old background permissions are secured; background symlinks are refused.
No passwordless sudo rules are installed. Three legacy managed drop-ins are
backed up and retired; the resulting sudoers configuration is checked by visudo.

## Restore login from a working TTY

Run these commands yourself, replacing the snapshot ID. The failed configuration
is moved to another backup, not deleted.

```bash
backup=/var/backups/shade-raid/REPLACE_WITH_SNAPSHOT_ID
sudo test -d "$backup"
sudo systemctl disable --now greetd
failed=$(sudo mktemp -d /var/backups/shade-raid/failed.XXXXXXXXXX)
sudo mv -- /etc/greetd "$failed/greetd"
if sudo test -e "$backup/greetd"; then
    sudo cp -a -- "$backup/greetd" /etc/greetd
fi
```

If `greetd.absent` exists in the snapshot, leave greetd disabled. Otherwise
inspect the restored configuration and re-enable greetd only if it was enabled
in your baseline. Keep the TTY open while testing login and logout before reboot.

Old sudoers files are retained as `sudoers.<name>` for inspection. They are not
needed by the new workflow. Do not restore old passwordless copy rules as routine
recovery. Any deliberate sudoers change must pass `visudo -cf FILE` before
installation as root:root mode 0440.

Login recovery is manual. This installer does not claim a global filesystem/service
transaction or protection against power loss. User theme recovery is described
in [the configuration migration guide](configuration-migration.md).

## CLI and package recovery

The CLI uses `~/.local/share/shade-raid/venv` (respecting XDG_DATA_HOME) and
`~/.local/bin/dotfiles`. Re-run `bash scripts/install-cli.sh` to rebuild it.
An unrelated existing entry point is preserved and causes a clear failure;
move it aside yourself if replacement is intended. The CLI resolves its installed
checkout; DOTFILES_DIR can explicitly override it.

Bash configuration, existing GTK bookmarks, a configured Git pager, and the
mirror list are preserved. SSH server setup requires `setup --ssh-server`.
Bootstrap saves pacman.conf in `/etc/pacman.conf.shade-raid-backup`, preserving
numbered previous backups. It performs a full system upgrade before package
installation. After a package failure, fix the reported package/network problem
and rerun. Never remove a database lock while a package manager is running.

Command logs: `~/.local/state/shade-raid/commands.jsonl`, mode 0600. Entries
include command, step, exit status and redacted diagnostics. Common credential
arguments and token formats are redacted; this is not a universal secret detector.

`bash scripts/bootstrap.sh --dry-run` makes no changes. Theme/action dry-runs
also avoid artifact/state writes, locks, child commands and reload threads.

## Required graphical smoke tests

- Login/logout through greetd and recovery through a separate TTY.
- Waybar, SwayNC, Walker and audio after a fresh login.
- Light/dark switching with no privilege prompt.
- Explicit login setup, then inspection of ownership and file modes.
- File pickers, browser screen sharing, notifications, clipboard and media.
- Actual Intel/AMD/NVIDIA hardware selection and repeated desktop setup.

Container checks cover installation commands, backups and file modes. They do
not validate PAM login, GPU/DRM, a graphical session or portal screen sharing.
