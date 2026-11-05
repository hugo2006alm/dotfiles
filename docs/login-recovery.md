# Explicit login changes and TTY recovery

Ordinary setup, configure and reload never install or refresh root login files.
Run these commands yourself in an interactive terminal as a normal user:

```sh
dotfiles setup-login
dotfiles repair-login-permissions
```

`setup-login` installs a stable validated snapshot of the three user login inputs
plus the fixed greetd session configuration. It accepts the shipped minimal Hyprland
login directives and ReGreet TOML, rejects linked/device/FIFO destinations and
unknown executable directives, checks the required root-owned executables and the
unprivileged greeter account, and refuses a conflicting display-manager alias.
Source symlinks must resolve inside the user's HOME or checkout. Custom login
configuration outside this supported template needs manual review; do not bypass
preflight simply to make a custom template install.

`repair-login-permissions` works without those source files, installed graphical
binaries, a greeter account or a completed migration. It secures existing regular
managed login files, including the legacy background, as root:root 0644. It validates
existing executable/session configuration before securing its contents. Missing
files are left missing. Unsafe linked directories/files require manual inspection.
A conflicting display manager does not prevent this narrowly scoped repair.

The generated ReGreet configuration uses the compositor/GTK background fallback,
with no image file dependency. Installation removes only the historical background
TOML section that points to `/etc/greetd/regreet-background.jpg`; another custom
resource path is refused for manual review. An existing legacy image is retained
and secured. No normal wallpaper or theme operation writes it.

Both operations perform an unprivileged read-only preflight before authentication.
The root helper repeats filesystem preconditions under its own global lock and
validates sudoers before changing login files. Inputs travel as immutable JSON,
not as a root-read user staging path. Prompts inherit the terminal; the earlier
command executor's captured authentication path is not used. The input lock is
`~/.shade-raid-locks/login-inputs.lock` (directory 0700, file 0600); configuration
writers and installers must acquire that same lock and never unlink its inode.
The privileged installation lock is `/run/shade-raid-login/install.lock`.

Each operation retains a private root-owned snapshot at
`/var/backups/shade-raid/login-ID/`. The directory is 0700, backup files and the
manifest are 0600, and original modes/owners are recorded in the manifest.
Every changed managed path is recorded before its effect. Ordinary failures and
handled SIGINT/SIGTERM/SIGHUP interruptions restore the original contents, modes,
owners and absence of files; a failed recovery retains state `recovery-required`
for inspection and retry. A failed repair can therefore restore previously insecure
legacy permissions: inspect the reported status and retry after fixing the cause.
Power loss and SIGKILL cannot run compensation; use the retained manifest/backup.
This is file recovery, not a transaction covering a running graphical session.

Only `/etc/sudoers.d/shade-raid` with the exact two historical user/HOME copy rules
and expected ownership is retired. Matching content under another name is kept.
Same-name custom rules, `plymouth_sync` and `regreet-theme` are backed up and kept
with an explicit manual-inspection message: no authenticated historical content is
known for the latter two names. Sudoers is validated again after changes; failure
restores retired rules too. Review any retained passwordless rules yourself.

## Enablement is explicitly manual

The installer never starts, stops, enables or disables any display manager. An
existing greetd alias/enablement is preserved, including on failure. From a working
recovery TTY in a disposable Arch VM, record the previous display-manager state,
review the installed files and choose when to enable greetd. Change a competing
manager only after planning how to restore it. Keep a second logged-in TTY open
until login, logout and a second login have all succeeded.

## Inspect and restore from a recovery TTY

Retain the printed snapshot ID. Review its `manifest.json`, especially `state`,
`originals` and `directory`. A non-interrupted recovery ends in `restored`.
For manual recovery, copy each recorded original from `greetd/` back to
`/etc/greetd/`, and each changed original sudoers file from `sudoers/` back to
`/etc/sudoers.d/`, using the recorded mode, uid and gid. Preserve a separate copy
of the failed current files first. A managed path marked `exists: false` must be
moved aside instead of retaining the new file. Restore only entries marked
`changed: true`; custom policy files were preserved and must remain preserved.
Run `visudo -c` yourself before using any restored sudoers configuration.

For a repeatable retry, inspect the checkout and backup first, replace the two
paths below, and run this yourself from the recovery TTY. The helper takes the
same root lock, uses the fixed whitelist and verifies backup hashes. Preserve the
failed files separately before a deliberate restore of an applied installation.

```sh
sudo /usr/bin/python3 -I -c '
import sys
from pathlib import Path
sys.path.insert(0, "/REVIEWED/CHECKOUT")
from dotfiles_api.infrastructure.login_installation import LoginInstallation
LoginInstallation().restore(Path(sys.argv[1]))
' /var/backups/shade-raid/login-REPLACE_WITH_ID
sudo visudo -c
```

Do not run recovery from an unreviewed writable checkout as root. Root recovery
commands must be run by the user, never by an unattended agent.

The backup records no enablement changes because none are performed. Restore any
manual display-manager activation separately using the state recorded beforehand.
Do not reboot into an untested configuration. Confirm fallback TTY access,
root ownership/modes, successful login/logout/login, ReGreet rendering, and
AMD/Intel/NVIDIA behavior in the VM. These graphical checks remain pending human
validation; parser/fixture tests do not establish that the desktop works.
