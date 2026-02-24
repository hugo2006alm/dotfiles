# SHADE RAID
### Hyprland rice · Arch Linux · ink-on-paper aesthetic

---

## WHAT THIS IS

A from-scratch Hyprland desktop built around a single visual idea: **ink on paper**. Hard borders, no blur, stark contrast, comic-panel window layout. Inspired by hand-drawn illustration and print design.

Built on Arch Linux. Uses [Omarchy](https://omarchy.org) as a reference point but shares no code with it.

---

## STACK

| Layer | Tool |
|---|---|
| WM | Hyprland |
| Bar | Waybar |
| Launcher | Walker |
| Terminal | Ghostty |
| Shell | Fish + Starship |
| Notifications | Mako |
| Wallpaper | swww |
| Lock screen | Hyprlock |
| Editor | Neovim + Antigravity |
| Browser | Zen |
| Audio | PipeWire + WirePlumber |
| Theme source | `~/.config/theme/colors.toml` |

---

## COLOR PALETTE

```
Background   #F4EFE4   paper
Background2  #EDE7D3   cream
Foreground   #0D0D0D   ink
Foreground2  #3A3A3A   ink faint
Accent       #D94F2B   red-orange
```

All colors live in `~/.config/theme/colors.toml`. Config files for Hyprland, Waybar, Mako, Hyprlock and others are generated from this single source of truth.

---

## INSTALL

On a fresh Arch install with `base-devel` and `git`:

```bash
bash <(curl -s https://raw.githubusercontent.com/YOURUSER/dotfiles/main/.config/setup/install.sh)
```

The script will:
1. Install `yay` (AUR helper)
2. Install all pacman and AUR packages
3. Clone this repo as a bare git repo into `~/.dotfiles`
4. Check out all dotfiles into `$HOME`
5. Generate Hyprland color config from `colors.toml`
6. Enable system services
7. Set fish as default shell

Log out and back in, then start Hyprland.

---

## DOTFILES MANAGEMENT

This repo uses the **bare git repo** method. No symlinks, no stow.

```bash
# The alias (already in your fish config after install)
alias dots='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'

# Common commands
dots status
dots add .config/hypr/hyprland.conf
dots commit -m "feat: ..."
dots push
```

---

## STRUCTURE

```
~/.config/
├── theme/
│   ├── colors.toml          # single source of truth for all colors
│   └── generate-hypr.sh     # generates ~/.config/hypr/colors.conf
├── hypr/
│   ├── hyprland.conf        # main config (sources the files below)
│   ├── colors.conf          # generated — do not edit manually
│   ├── keybinds.conf        # all keybindings
│   ├── windowrules.conf     # float, workspace, opacity, size rules
│   └── autostart.conf       # exec-once entries
├── waybar/
├── mako/
├── ghostty/
├── starship.toml
└── setup/
    └── install.sh           # bootstrap script
```

---

## KEY BINDINGS

| Bind | Action |
|---|---|
| `Super + Enter` | Terminal |
| `Super + Space` | Launcher |
| `Super + E` | File manager |
| `Super + L` | Lock screen |
| `Super + Q` / `Alt + F4` | Close window |
| `Super + F` | Fullscreen |
| `Super + V` | Toggle float |
| `Super + 1-0` | Switch workspace |
| `Super + Shift + 1-0` | Move window to workspace |
| `Super + Arrows` | Move focus |
| `Super + Shift + Arrows` | Move window |
| `Super + Ctrl + Arrows` | Resize window |
| `Print` | Screenshot (full) |
| `Shift + Print` | Screenshot (region) |
| `Ctrl + Print` | Screenshot to clipboard |

---

## WORKSPACE LAYOUT

| WS | App |
|---|---|
| 1 | Zen (browser) |
| 2 | Ghostty (terminal) |
| 3 | Vesktop (Discord) |
| 4 | Antigravity (editor) |
| 9 | Spotify |
| 10 | Steam / Heroic |

---

## AFTER INSTALL — VERIFY CLASS NAMES

Once in Hyprland, run:

```bash
hyprctl clients
```

Check that window classes match what's in `windowrules.conf`. Key ones to verify: `zen-browser`, `antigravity`, `com.mitchellh.ghostty`.

---

## REGENERATING COLORS

If you update `colors.toml`:

```bash
bash ~/.config/theme/generate-hypr.sh
hyprctl reload
```

---
