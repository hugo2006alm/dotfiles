# Shade Raid v2 checkpoint

Baseline: `5b95d81`. Steps 01–10 of the supplied 15-step roadmap are implemented.
Desktop acceptance checks remain pending; the full roadmap is not complete.

| Step | Changes | Desktop acceptance still pending |
| --- | --- | --- |
| 01 | Explicit interactive login setup, private staging, root-owned files and recovery snapshots; no privileged theme reload | greetd login/logout and TTY recovery |
| 02 | Subparsers, command-local flags, legacy flag positions, quoted SwayNC theme actions, Fish CLI aliases | Theme selection in running SwayNC |
| 03 | Required/optional/query execution; install/link errors propagate; source preflight; private redacted JSON logs | Clean Arch VM install and interruption recovery |
| 04 | Shared hardware-aware profile resolution, venv bootstrap, preserved personal files, opt-in SSH server | Real GPU hardware and repeated desktop setup |
| 05 | Dedicated home/ Stow package, no directory folding, migration backups, generated/runtime state outside source | Migration on the actual desktop after backup |
| 06 | Pure execution plans, no dry-run writes/commands/threads, fresh-HOME preview and global safety flags | Review planned changes against the actual machine |
| 07 | One theme coordinator, atomic replacements, recoverable journals, automatic failure recovery and explicit rollback | Theme/rollback smoke tests in Hyprland |
| 08 | Typed application registry; packages, dependency/output validation and CLI composition | Confirm installed application requirements |
| 09 | Four staged Sass compilations, transactional CSS, native notification reload and unchanged-content refresh detection | Visual checks in each themed application |
| 10 | Environment import before user services, native session target lifetime, one non-disruptive portal activation path | Login/logout, duplicate checks, file chooser and active screen-sharing through theme toggles |

See [application contracts](application-registry.md), [style compilation](theme-styling.md)
and [session migration and live smoke tests](wayland-session.md).

## Checks

```bash
python -m unittest discover -s dotfiles_api/tests
find scripts home .config -name '*.sh' -print0 | xargs -0 -r shellcheck
fish -n home/.config/fish/config.fish
```

Only in a disposable Arch container, as root:

```bash
SHADE_RAID_DISPOSABLE_ARCH=1 python -m unittest dotfiles_api.tests.test_arch_login_integration
```

This opt-in test modifies the container's /etc/greetd. Its executor runs the
underlying file-install commands directly as container root, never invoking sudo
or authenticating on the host. systemctl enable is replaced by a recorded result.
It checks old mode-0666 files, backup contents, symlink replacement without
overwriting external data, root ownership, mode 0644 and repeated application.

## Remaining steps

11. Composable profiles and persisted selections.
12. Daily desktop actions and ergonomics.
13. Read-only doctor and explicit repair plans.
14. Broader CI, integrations and graphical smoke matrix.
15. Asset/code cleanup, documentation and safer push helper.

The existing dotfiles_push helper stages and pushes everything and invokes the
HOME linker. It is unsuitable for an isolated implementation checkout; explicit
file staging and an explicit branch keep this checkpoint reviewable. Its planned
replacement remains step 15. Do not combine login, Stow and session migrations.
