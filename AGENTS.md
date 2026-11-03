# Shade Raid — Configuration Guide for Agents

## Dotfiles Setup
- **Stow:** Repository root is `~/dotfiles/`; only the `home/` package is stowed, with `--no-folding`.
- **Fish function:** Always use `dotfiles_push "commit message"` to apply changes. This function switches to the folder, commits, pushes, and runs stow.

## Color Palette
Single source of truth is `~/.config/themes/shade-raid/colors.toml`.
- `background`: `#F4EFE4` (paper)
- `background2`: `#EDE7D3` (cream)
- `foreground`: `#0D0D0D` (ink)
- `foreground2`: `#3A3A3A` (ink faint)
- `accent`: `#D94F2B` (red-orange)
- `accent_fg`: `#F4EFE4`
- `inactive`: `#C8C2B4`

## Python Modular Dotfiles API & Generator Pattern
All theme generation, linking, package installation, and reloading is managed by the Python modular API located in `dotfiles_api/`.

### Key Constraints:
1. **Single Class Per File:** Every generator class, reloadable, service, or model must reside in its own separate Python file with a name corresponding to the class/system it manages. Do not bundle multiple classes together.
2. **Strict Test-Driven Development (TDD):** Always follow TDD. Write failing tests in `dotfiles_api/tests/` first (e.g. testing rendering outputs, command execution strings, or CLI arguments), and then implement code to make them pass.
3. **Running Tests:** Run the test suite using:
   ```bash
   python -m unittest discover -s dotfiles_api/tests
   ```
4. **Generator Registry:** Concrete app-specific generators inherit from `BaseGenerator` and reside under `dotfiles_api/infrastructure/generators/`. They must implement `render()` and return `list[GeneratedArtifact]`.
5. **Reloadable Registry:** Concrete app-specific reloaders inherit from `Reloadable` and reside under `dotfiles_api/infrastructure/reloadables/`. They must implement `reload()`.
6. **Integration Point:** Declare packages, dependencies, generator, outputs, validator and reload factory in `dotfiles_api/infrastructure/application_catalog.py`. The typed ApplicationRegistry validates contracts and composes the CLI. Do not add parallel app lists to the CLI or desktop profile.
7. **Theme application:** Full theme changes use ThemePlanner and ThemeCoordinator. Generate/validate everything before a file transaction; update active state last. Do not write generated output into the repository or mutate runtime state from render().
8. **Dry-run:** Never create directories, files, locks, logs, threads or subprocesses in a dry-run path. Preserve this contract on errors too.
9. **Styles and sessions:** Declare compiled styles in the application spec. Compile before installing any theme artifact; reloaders never write CSS. Persistent app services use namespaced user units bound to Hyprland's native session target. Theme changes never restart portals; `dotfiles action portal` only ensures activation.
10. **Diagnostics and repair:** Doctor and repair previews are read-only: no command logs, locks, writes, compiler runs or service activation. Dry-run also defers read-only subprocess queries. Apply only the reviewed plan ID and the fixed user-level recipes; package/root/permission repairs remain manual.

## Tech Stack
- **WM:** Hyprland (0.55+ using Lua wrapper configuration)
- **Bar:** Waybar (compiled from SCSS to CSS via `sassc`)
- **Terminal:** Ghostty + Fish + Starship
- **Launcher:** Walker
- **Notifications:** SwayNC
- **Wallpaper:** awww
- **Browser:** Zen (`zen-browser-bin`)
- **Discord:** Vesktop (`vesktop-bin`)
- **AUR Helper:** yay

## Shell Constraints
- **Fish Shell:** Heredoc syntax (`<<EOF`) is NOT supported in Fish. Use `echo 'content' > file` or write files from Bash scripts instead.

## Hardware Setup
Desktop system (no battery, no touchpad). Monitor is 2560×1440 @ 144Hz with scaling set to 1.6. Keyboard layout is PT.

## CRITICAL SECURITY RULE: FAILLOCK PREVENTION
- **NEVER** run commands containing `sudo`, `yay`, or `su` in background tasks or non-interactive shells. This instantly triggers Arch Linux's `pam_faillock` module because it cannot prompt for a password, permanently locking the user out of their own system for 10 minutes after 3 failed attempts. Always ask the user to run `sudo` commands themselves.
