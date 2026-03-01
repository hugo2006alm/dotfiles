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
| Editor | Neovim |
| Browser | Zen |
| Audio | PipeWire + WirePlumber |
| Theme source | `~/.config/themes/shade-raid/colors.toml` |

---

## COLOR PALETTE

```
Background   #F4EFE4   paper
Background2  #EDE7D3   cream
Foreground   #0D0D0D   ink
Foreground2  #3A3A3A   ink faint
Accent       #D94F2B   red-orange
```

All colors live in `~/.config/themes/shade-raid/colors.toml`. Config files for Hyprland, Waybar, Mako, Hyprlock, Ghostty and others are generated from this single source of truth via `generate.sh`.

---

## INSTALL

On a fresh Arch install with `base-devel` and `git`:

```bash
bash <(curl -s https://raw.githubusercontent.com/hugo2006alm/dotfiles/main/.config/install/install.sh)
```

The script will:

1. Install `yay` (AUR helper)
2. Enable multilib and install all pacman + AUR packages
3. Set up SSH key and clone this repo as a bare git repo into `~/.dotfiles`
4. Check out all dotfiles into `$HOME`
5. Enable system services (NetworkManager, bluetooth, pipewire, ufw, autologin)
6. Set fish as default shell, configure git, refresh mirrors and fonts
7. Generate and apply the Shade Raid theme

Log out and back in — Hyprland starts automatically on TTY1.

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
├── themes/
│   ├── generate.sh              # generates all color configs from colors.toml
│   ├── apply.sh                 # generate + reload everything
│   └── shade-raid/
│       └── colors.toml          # single source of truth for all colors
├── hypr/
│   ├── hyprland.conf            # main config
│   ├── colors.conf              # generated — do not edit manually
│   ├── keybinds.conf            # all keybindings
│   ├── windowrules.conf         # float, workspace, opacity, size rules
│   └── autostart.conf           # exec-once entries
├── waybar/
│   ├── config.jsonc             # module layout
│   └── style.scss               # styles (compiled to style.css on apply)
├── mako/
├── ghostty/
├── starship.toml
└── install/
    ├── install.sh               # orchestrator
    ├── packages.sh              # pacman + AUR
    ├── dotfiles.sh              # SSH, clone, checkout
    ├── services.sh              # systemctl + autologin
    ├── user.sh                  # shell, git, fonts, mirrors
    ├── theme.sh                 # generate theme
    └── extras.sh                # spicetify, optional stuff
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
| 4 | Neovim |
| 9 | Spotify |
| 10 | Steam / Heroic |

---

## AFTER INSTALL — VERIFY CLASS NAMES

Once in Hyprland, run:

```bash
hyprctl clients
```

Check that window classes match what's in `windowrules.conf`. Key ones to verify: `zen-browser`, `com.mitchellh.ghostty`, `vesktop`.

---

## REGENERATING COLORS

If you update `colors.toml`:

```bash
~/.config/themes/apply.sh shade-raid
```

This regenerates all color configs and reloads Hyprland, Waybar and Mako automatically.
```

Then commit:
```bash
dots add README.md
dots commit -m "docs: update README for new theme system and install structure"
dots push
