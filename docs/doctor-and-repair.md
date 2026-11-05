# Read-only diagnostics and reviewed repairs

```sh
dotfiles doctor
dotfiles doctor --json
dotfiles repair --plan
dotfiles repair --apply --plan-id ID_FROM_THE_REVIEWED_PLAN
```

`doctor` inspects saved software selections and pacman's local inventory,
generated outputs and supported syntax, compiled stylesheet fingerprints, Stow
links, private state permissions, login configuration ownership/modes, user
services, portal health and tracked Git changes. It reports unknown checks when
outside Wayland or when a query cannot establish health. Core-only saved profiles
do not create false missing-desktop-output diagnoses. Optional profiles are
checked when selected; missing apps are not silently installed.

Diagnostics do not write files, log query commands, acquire locks, compile Sass,
contact package repositories, start services or run privileged commands. Git
status disables optional index locks and fsmonitor hooks. Service status queries
use only `systemctl --user is-active`. They bypass the normal command writer/log
context deliberately. `--dry-run` also defers these subprocess queries entirely.
JSON contains version, exit_code and structured findings; errors return status 1,
warnings/unknown checks alone return 0. Unknown does not mean healthy.

Normal compilation records deterministic source/input and CSS-payload digests in
CSS comments. Doctor recomputes those hashes without compiling or writing scratch
files. Missing metadata from older checkpoints is diagnosed as requiring a normal
configure. JSON/TOML/INI use in-process parsers; stylesheet checks cover hash
integrity and delimiter/string structure, not a complete GTK/Hyprland parser.

`repair --plan` is read-only and lists concrete commands, affected paths and a
SHA-256 plan ID. To apply, review that output and invoke `--apply --plan-id ID`.
The service recomputes the report, including observed/expected content hashes,
and rejects changed plans before running an operation. A dry-run plan contains
deferred checks and must be reviewed again without dry-run before application.

Automatic recipes are limited to Stow linking, transactional theme configure,
session service startup and non-disruptive portal activation. Linking precedes
configuration; configuration precedes session startup. These use the same normal
safety/error handling and rollback mechanisms as their CLI commands. A failed
recipe stops later recipes. They are not a global transaction with external
services. Generated-file repair can replace personal edits in generated outputs;
the review identifies those paths, and file transactions retain recovery data.
Personal overrides of static Stow sources are reported without an overwrite recipe.

Package installation, root/login setup and permission changes are always printed
as manual repairs and never executed by this command, even with --apply. Run
needed package/root commands yourself in an interactive terminal, then generate
a new repair plan. Insecure greetd ownership, writable modes and symlinks require
explicit login recovery/setup. Doctor never attempts automatic chmod or sudo.

Applying a repair acquires the standard configuration lock. A missing plan ID is
rejected before creating that lock. Remaining manual issues are reported after
application and may leave a nonzero exit status even when user-level fixes succeed.

The Arch integration deletes compiled CSS, verifies the real CLI repair preview
leaves HOME unchanged, then applies the reviewed plan and verifies the restored
stylesheet. Other tests cover stale plan refusal, no privileged callbacks, real
compiled-CSS tampering detection, read-only CLI snapshots and deferred dry-run
queries. Real graphical diagnosis, user services and root recovery still need
the live smoke tests in `daily-desktop.md` and `wayland-session.md`.
