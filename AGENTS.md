# Shade Raid — Configuration Guide for Agents

## Dotfiles Setup
- **Stow:** Managed via GNU Stow. Dotfiles root is `~/dotfiles/`.
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
6. **Integration Point:** All new generators and reloadables must be instantiated and registered inside `dotfiles_api/presentation/cli.py` and have their paths mapped in `artifact_paths` inside `main()`.

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
