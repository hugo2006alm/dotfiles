# Shade Raid v2 checkpoint

Baseline: `5b95d81`. This checkpoint implements milestone A (steps 01–04) of the
supplied 15-step roadmap. It does not mark the entire roadmap complete.

| Step | Changes | Desktop acceptance still pending |
| --- | --- | --- |
| 01 | Explicit interactive login setup, private staging, root-owned files and recovery snapshots; no privileged theme reload | greetd login/logout and TTY recovery |
| 02 | Subparsers, command-local flags, legacy flag positions, quoted SwayNC theme actions, Fish CLI aliases | Theme selection in running SwayNC |
| 03 | Required/optional/query execution; install/link errors propagate; source preflight; private redacted JSON logs | Clean Arch VM install and interruption recovery |
| 04 | Shared hardware-aware profile resolution, venv bootstrap, preserved personal files, opt-in SSH server | Real GPU hardware and repeated desktop setup |

## Checks

```bash
python -m unittest discover -s dotfiles_api/tests
find scripts .config -name '*.sh' -print0 | xargs -0 -r shellcheck
fish -n .config/fish/config.fish
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

05. Declarative `home/` layout and safe Stow migration.
06. Fully side-effect-free dry-run and execution plans.
07. Coordinated theme validation, staging, rollback and state updates.
08. Typed application registry.
09. Unified compilation and selective reloads.
10. Wayland environment, portals and user services.
11. Composable profiles and persisted selections.
12. Daily desktop actions and ergonomics.
13. Read-only doctor and explicit repair plans.
14. Broader CI, integrations and graphical smoke matrix.
15. Asset/code cleanup, documentation and safer push helper.

The existing dotfiles_push helper stages and pushes everything and stows the
user's HOME. It is unsuitable for an isolated implementation checkout; explicit
file staging and an explicit branch keep this checkpoint reviewable. Its planned
replacement remains step 15. Do not combine login, Stow and session migrations.
