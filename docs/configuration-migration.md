# Configuration layout, execution plans and theme recovery

## Layout

- `home/`: declarative Stow package. Stow uses `--no-folding`.
- `dotfiles_api/`, `scripts/`, `docs/`: implementation, bootstrap and documentation.
- `templates/legacy/`: old generated greetd/SwayNC defaults retained solely for
  recovery when the former tracked paths have disappeared during an update.
- Generated configuration: real files in the user's configuration directories.
- Active theme, generated Plymouth script and transaction journals:
  `${XDG_STATE_HOME:-$HOME/.local/state}/shade-raid/`.
- Preview/PID state: `$XDG_RUNTIME_DIR/shade-raid/`, or the state's `runtime/`
  directory if XDG_RUNTIME_DIR is unavailable.
- CLI locks: the XDG runtime directory, or `~/.shade-raid-locks/`. Persistent
  lock inodes are retained to avoid unlink/recreate races.

## Migrating an existing checkout

Before pulling the layout change, back up affected HOME configuration and local
files inside the repository's old .config/.local folders. Keep the old Git
revision and a working TTY available. Git cannot recover untracked files that
were deleted before migration.

Run `dotfiles link --dry-run` to inspect the intended command and legacy links.
Run `dotfiles link` to migrate. Only links owned by the old/current repository
layout are unfolded. Real personal files are not adopted or overwritten; Stow
reports conflicts. Unmanaged directory symlinks are refused.

Each actual legacy migration creates `~/.shade-raid-backups/stow-ID/`, including
the original link destinations and available source contents. The folder is kept
outside .local because old installations may have .local itself folded. A failed
link operation restores old links and removes newly created managed links.
Successful repeated linking creates no additional migration backup.

If manual recovery is required, inspect manifest.json and its contents/ tree,
restore the affected original link destinations, and retain personal/generated
files from the snapshot. Do not run git clean against old generated data before
the HOME migration and its backup have been verified.

## Previewing a theme

```bash
dotfiles --dry-run configure --theme shade-raid-dark
dotfiles setup --dry-run
dotfiles action screenshot --region --dry-run
```

The planner renders outputs, validates destinations and supported syntax, and
compares contents. It does not write artifacts, active state, preview files,
locks, logs, staging directories, PID files, or start application commands/threads.
Errors also leave application files unchanged. Fresh-HOME setup previews can
read declarative themes directly from the repository without running Stow.
An explicit `--` ends global flag handling and forwards remaining action flags.

JSON, TOML and INI are parsed in-process. Stylesheets receive delimiter/string
checks. These checks do not replace application-specific compilation; complete
SCSS compilation and application integration remain step 09.

## Applying and restoring themes

The coordinator renders and validates all generators before staging a batch.
It records original bytes, permissions, timestamps, symlink targets and absent
files, then replaces each changed file atomically. Preview and active theme state
are part of the same recovery batch; active state is written last. Ordinary
exceptions and interruptions trigger restoration. Newly created outputs are
removed, and empty directories created for them are cleaned up.

```bash
dotfiles configure --theme shade-raid-dark
dotfiles rollback --dry-run
dotfiles rollback
```

Journals remain under the state's transactions/ folder. Rollback restores the
most recent committed or interrupted prepared batch. It refuses newer personal
content edits instead of overwriting them. A failed restoration raises an error
with the retained journal location; resolve the filesystem problem and retry.
An unchanged theme avoids additional journals and application/wallpaper refreshes.

Application refreshes happen after the file commit. A refresh failure is reported
explicitly; use reload or rollback after fixing the application/service problem.
Filesystem replacements and external services are not one global transaction.
The journal supports recovery but does not promise atomic multi-file application
or absolute recovery guarantees during power loss.

Test migration in a temporary HOME, then verify theme switching and recovery in
a real Hyprland session before migrating the main desktop.
