# Recovery and installation notes

Test in a disposable Arch VM first. Keep a second logged-in TTY available and
record the current display-manager configuration before making login changes.

Normal setup, configure and reload do not install greetd files. The explicit
`dotfiles setup-login` command performs preflight and keeps a private recovery
snapshot. It does not enable, disable, start or stop a display manager. Review
[login-recovery.md](login-recovery.md) for exact snapshot inspection and
restoration instructions. It also describes the separate
`dotfiles repair-login-permissions` operation and the handling of custom sudoers.
Do not remove or restore sudoers rules without inspecting them and validating
changes with `visudo`.

The CLI lives in `~/.local/share/shade-raid/venv` (respecting `XDG_DATA_HOME`)
and `~/.local/bin/dotfiles`. Re-run `bash scripts/install-cli.sh` to rebuild it.
An unrelated existing launcher is preserved and causes a clear error.

Bootstrap checks the destination and the multilib requirement before package
installation. It does not edit pacman.conf. A full system upgrade is performed
only when `--upgrade-system` is explicitly requested. Fish login-shell changes
require `setup --change-shell`; SSH server enablement requires `--ssh-server`.
Firewall access remains a separate user decision.

Command logs are stored at `~/.local/state/shade-raid/commands.jsonl`, mode 0600.
Sensitive launch arguments are redacted; avoid putting secrets in command lines.
Dry runs avoid the documented effects, but cannot prove that a graphical session,
portal, login, clipboard or recording works. Validate those in a real Arch/Hyprland
session using the plan's manual checks.
