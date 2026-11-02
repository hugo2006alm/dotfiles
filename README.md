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
| Notifications | SwayNC |
| Wallpaper | awww |
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

All colors live in `~/.config/themes/shade-raid/colors.toml`. Config files for Hyprland, Waybar, SwayNC, Hyprlock, Ghostty and others are generated from this single source of truth via the Python Modular Dotfiles API.

---

## INSTALL

On a fresh Arch install with `base-devel` and `git`:

```bash
git clone https://github.com/hugo2006alm/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash .config/install/install.sh
```

The script will:
1. Install `yay` (AUR helper)
2. Enable multilib and install all pacman + AUR packages
3. Link declarative files from home/ using GNU Stow without directory folding
4. Enable system services (NetworkManager, bluetooth, pipewire, ufw)
5. Set fish as default shell, preserve existing personal preferences, refresh fonts
6. Generate and apply the Shade Raid theme using the Python API

The CLI runs in a private Python virtual environment, exposed through
`~/.local/bin/dotfiles`. Add `~/.local/bin` to your graphical session's PATH;
Fish configuration already includes it. Run the bootstrap in an interactive
terminal as a normal Arch user. Optional flags: `--github` and `--ssh-server`.
`bash scripts/bootstrap.sh --dry-run` previews bootstrap without making changes.

Login installation is separate: review [recovery instructions](docs/recovery.md),
test in an Arch VM, then run `dotfiles setup-login` yourself in a terminal.
Keep a working TTY open and verify login/logout before rebooting. Automatic
theme changes never install files into /etc/greetd.

See [Shade Raid v2 progress and remaining steps](docs/shade-raid-v2.md).

---

## DOTFILES MANAGEMENT

GNU Stow manages only the declarative `home/` package, using `--no-folding`.
Configuration directories remain real directories so generated files can live
beside linked source files. Python code, Git metadata, scripts and documentation
are not part of the Stow package.

Run `dotfiles link` to install links. Legacy repository-owned directory links
are unfolded with recovery snapshots under `~/.shade-raid-backups/`.
Conflicting personal files are preserved; a failed migration restores old links.
Back up affected configuration before updating an existing installation.

To make changes, edit the files inside `~/dotfiles/` and run the custom Fish helper to commit, push, and re-apply:

```bash
# Commit, push to origin/main, and run stow automatically
dotfiles_push "commit message"
```

---

## PYTHON CLI MANAGER (`dotfiles_api`)

Theme generation, application linking, package installation, and live reloading are fully orchestrated by a clean-architecture Python CLI.

### Usage
```bash
python -m dotfiles_api.presentation.cli [OPTIONS] COMMAND
```

### Options
- `--dry-run`: Builds the theme execution plan without writing artifacts, active state, locks or logs, starting reload threads, or launching child commands. Works before/after subcommands and after action arguments (before an explicit `--` delimiter).
- `--theme`: The theme name to apply (default: `shade-raid`).

### Commands
- `install`: Installs the system packages defined in the active profile.
- `link`: Runs the stow linking step.
- `configure`: Generates all configuration files for registered applications from the theme tokens.
- `reload`: Reloads all active desktop applications (Waybar, SwayNC, Hyprland, Ghostty, Walker, etc.).
- `apply-all`: Performs install, link, configure, and reload commands sequentially.
- `toggle`: Switches the theme dynamically between light and dark variants (e.g. `shade-raid` <-> `shade-raid-dark`).
- `setup --github`: Runs setup and explicitly requests interactive GitHub authentication.
- `setup --ssh-server`: Explicitly enables the SSH server and its firewall rule.
- `setup-login`: Explicit interactive installation of root-owned greetd files, with backups.
- `rollback --dry-run`: Inspect the most recent recoverable theme journal without changes.
- `rollback`: Restore its original files, permissions, timestamps and active theme.

Theme application renders and validates artifacts before staging and individual
atomic replacements. Changed files and active state form one recoverable batch.
An apply failure or interruption restores existing files and removes newly
created ones. Unchanged themes do not refresh applications or wallpapers.
Journals are kept under `~/.local/state/shade-raid/transactions/`, respecting
XDG_STATE_HOME. Refresh failures are reported after the file commit and can be
handled with `reload` or `rollback`; files and running services are not a global
transaction.

---

## SYSTEM CONFIGURATION MAPPINGS

| Target Config | Generator | Output Path |
|---|---|---|
| Hyprland Colors | `HyprlandGenerator` | `~/.config/hypr/colors.lua` & `colors.conf` |
| Hyprland Style | `HyprlandGenerator` | `~/.config/hypr/style.lua` & `style.conf` |
| Waybar Colors | `WaybarGenerator` | `~/.config/waybar/colors.scss` |
| Ghostty Colors | `GhosttyGenerator` | `~/.config/ghostty/colors.conf` |
| SwayNC Style | `SwayncGenerator` | `~/.config/swaync/style.css` |
| SwayOSD Colors | `SwayosdGenerator` | `~/.config/swayosd/_colors.scss` |
| Btop Configuration | `BtopGenerator` | `~/.config/btop/btop.conf` & `shade-raid.theme` |
| Walker Config | `WalkerGenerator` | `~/.config/walker/config.toml` & `_colors.scss` |
| wlogout Colors | `WlogoutGenerator` | `~/.config/wlogout/_colors.scss` |
| Vesktop Theme | `VesktopGenerator` | `~/.config/vesktop/themes/{theme_name}.theme.css` |
| Hyprlock Config | `HyprlockGenerator` | `~/.config/hypr/hyprlock.conf` |
| ReGreet Style | `ReGreetGenerator` | `~/.config/greetd/regreet.css` |
| greetd Config | `GreetdGenerator` | `~/.config/greetd/regreet.toml` (installed explicitly by `setup-login`) |
| GTK Settings | `GtkGenerator` | `~/.config/gtk-3.0/settings.ini` & `gtk-4.0/settings.ini` |
| GTK Stylesheet | `GtkGenerator` | `~/.config/gtk-3.0/gtk.css` & `gtk-4.0/gtk.css` |
| Plymouth Script | `PlymouthGenerator` | `~/.local/state/shade-raid/generated/plymouth/shade-raid.script` |

---

## DEVELOPER TUTORIAL

The project is structured following Domain-Driven Design (DDD) principles:
- `dotfiles_api/domain/`: Core model structures, design token definitions, and events.
- `dotfiles_api/context/`: Execution context (handling dry-runs) and environmental context.
- `dotfiles_api/application/`: High-level services (Install, Theme, Reload), storage interfaces, and config transactions.
- `dotfiles_api/infrastructure/`: Concrete package sources, symlinkers, file stores, generators, and reloadables.
- `dotfiles_api/presentation/`: Entry points including the CLI execution logic.

### 1. Project Constraints
- **Single Class Per File:** Each generator, reloadable, or utility must live in its own dedicated Python file named after the class/system it manages.
- **Strict TDD:** Implement failing unit tests first, and only write code once you have a failing test. Run the test suite:
  ```bash
  python -m unittest discover -s dotfiles_api/tests
  ```

### 2. Adding a New Theme
1. Create a folder named after your theme: `~/.config/themes/<theme_name>/`.
2. Add a flat `colors.toml` file containing your palette:
   ```toml
   background = "#F4EFE4"
   foreground = "#0D0D0D"
   accent = "#D94F2B"
   ...
   ```
3. The global styling configuration is managed in `~/.config/themes/style.toml`.

### 3. Creating a New Configuration Generator
1. Create a new file under `dotfiles_api/infrastructure/generators/<app_name>.py`.
2. Declare a class extending `BaseGenerator` implementing `render()`:
   ```python
   from dotfiles_api.domain.tokens import DesignTokens
   from dotfiles_api.domain.artifacts import GeneratedArtifact
   from dotfiles_api.infrastructure.generators.base import BaseGenerator

   class AppGenerator(BaseGenerator):
       def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
           content = f"background = {tokens.colors.colors['background']}"
           return [GeneratedArtifact(artifact_id="app-config", content=content)]
   ```
3. Define the physical path in `artifact_paths` inside `dotfiles_api/presentation/cli.py`.
4. Instantiate the generator and subscribe it to `ThemeChangedEvent` in `cli.py`.

### 4. Creating a New Reloadable
1. Create a new file under `dotfiles_api/infrastructure/reloadables/<app_name>.py`.
2. Declare a class extending `Reloadable` implementing `reload()`:
   ```python
   from dotfiles_api.domain.contracts.reloadable import Reloadable
   from dotfiles_api.context.execution import ExecutionContext

   class AppReloadable(Reloadable):
       def __init__(self, exec_ctx: ExecutionContext) -> None:
           self._exec = exec_ctx

       def reload(self) -> None:
           self._exec.execute(["pkill", "-x", "app"])
   ```
3. Instantiate and register it in `cli.py` inside the `reloadables` list.

---

## ISSUES & CONTRIBUTIONS

We welcome bug reports and feature requests!
1. Check the existing issues before opening a new one.
2. Use the provided templates:
   - **Bug Report:** Use the [Bug report template](.github/ISSUE_TEMPLATE/bug_report.md) to detail reproducing steps and environment information.
   - **Feature Request:** Use the [Feature request template](.github/ISSUE_TEMPLATE/feature_request.md) to describe new application configuration generators or reloadables.

---

## LICENSE

This repository is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for the full text.

Copyright (c) 2026 Hugo Almeida.
