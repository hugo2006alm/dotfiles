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

## Generator Pattern
Themes for individual apps are generated using `~/.config/themes/generate.sh`. 
- **Rule:** Do NOT create separate generator files for new apps; append them to the existing `generate.sh`.
- Use the provided bash functions `get <key>` and `hex <key>` to retrieve colors.
- Generated output files should be added to `.gitignore`, whereas the generator templates themselves are tracked.

## Tech Stack
- **WM:** Hyprland (0.55+ using Lua wrapper configuration)
- **Bar:** Waybar (compiled from SCSS to CSS via `sassc`)
- **Terminal:** Ghostty + Fish + Starship
- **Launcher:** Walker
- **Notifications:** Mako
- **Wallpaper:** swww
- **Browser:** Zen (`zen-browser-bin`)
- **Discord:** Vesktop (`vesktop-bin`)
- **AUR Helper:** yay

## Shell Constraints
- **Fish Shell:** Heredoc syntax (`<<EOF`) is NOT supported in Fish. Use `echo 'content' > file` or write files from Bash scripts instead.

## Hardware Setup
Desktop system (no battery, no touchpad). Monitor is 2560×1440 @ 144Hz with scaling set to 1.6. Keyboard layout is PT.

## CRITICAL SECURITY RULE: FAILLOCK PREVENTION
- **NEVER** run commands containing `sudo`, `yay`, or `su` in background tasks or non-interactive shells. This instantly triggers Arch Linux's `pam_faillock` module because it cannot prompt for a password, permanently locking the user out of their own system for 10 minutes after 3 failed attempts. Always ask the user to run `sudo` commands themselves.
