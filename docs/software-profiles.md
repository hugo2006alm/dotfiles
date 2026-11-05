# Software profiles and incremental installs

`desktop` remains the default. Select profiles explicitly, repeat the flag to
combine them, and review the same plan without processes or writes:

```sh
dotfiles install --profile daily --profile dev --dry-run
dotfiles install --profile daily --profile dev
dotfiles install --profile gaming --package obs-studio
```

Profiles: `core` (shell/base tools), `appearance` (fonts/icons, depends on core),
`desktop` (Wayland, depends on core and appearance), `daily` (desktop plus Zen,
Vesktop and Bitwarden), `dev` (core plus editor, uv and Docker), `gaming` (desktop
plus Steam), and `ai` (core plus generic Ollama). No ROCm/CUDA hardware is assumed
by the AI profile. Docker/Ollama installation does not enable their daemons or
grant group memberships automatically. Steam needs a configured repository that
provides it (normally multilib); the planner reports unavailable packages.

Application packages/source overrides remain in the central catalog. Profile
dependencies are resolved once, duplicates removed, and detected GPU packages
included only with a desktop. Optional apps are attached to explicit profiles;
they are absent from the default desktop. Legacy optional package selection in
interactive setup still works; `--package` adds explicit choices.

The installer reads pacman's local inventory, skips already installed packages,
and checks all pending package sources before installing any group. Known AUR
packages found in official repositories use pacman. AUR existence is checked by
HTTPS metadata, never by running yay in a background query. An unavailable helper,
package or metadata endpoint stops the plan with a clear error. Repository sync
state is not changed by planning; use the normal full-system upgrade workflow
when refreshing stale databases. No partial `pacman -Sy` upgrade is introduced.

Normal application prints INSTALL PLAN before installation. Dry-run defers source
availability checks and starts neither subprocesses nor network requests. The
`--needed` package-manager safeguard remains in addition to inventory filtering.
Run real installs yourself in an interactive terminal so privilege prompts work.

After every requested installation group succeeds, the installer atomically
merges selected profiles, desired packages and explicit optional choices into
`$XDG_STATE_HOME/shade-raid/installation.json` (default `~/.local/state`). Failure
preserves the previous selection. Actual packages may have been installed before
a later failure; retry reads inventory and skips them. This command does not
perform system upgrades or uninstall packages from older selections.

Use `install` for isolated profile additions. `setup` remains the complete desktop
bootstrap: select `desktop` or a profile depending on it, alongside any additions
(for example `setup --profile desktop --profile dev`). Core-only setup is rejected
before installation; use `install --profile core` for a headless system.

Source contracts follow [pacman query/sync semantics](https://man.archlinux.org/man/pacman.8.en)
and [AUR v5 metadata routing](https://github.com/archlinux/aurweb/blob/master/aurweb/routers/rpc.py).
