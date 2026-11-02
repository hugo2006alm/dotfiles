# Wayland session services

Shade Raid uses Hyprland's packaged `hyprland-session.target`. Current Hyprland
starts/stops this target itself and binds it to `graphical-session.target`. No
replacement target or UWSM requirement is introduced. Builds without that native
integration need upgrading or a separately validated session manager before this
service migration is applied. Keep the old desktop checkout available until the
login smoke tests below pass.

At `hyprland.start`, `dotfiles action session` imports an explicit allowlist of
session variables into D-Bus and user systemd, reloads unit definitions, and starts
the units declared by the application registry. The allowlist includes the Wayland
display, desktop identity, instance signature, PATH, XDG_DATA_DIRS and optional X11
authentication variables; it does not import arbitrary shell secrets. Commands
run in order and a failed import stops dependent startup.

Waybar, SwayNC, Walker, Elephant and SwayOSD have one owner: namespaced user units.
They bind to the native Hyprland target, stop with the graphical session, limit
failure restart loops, and skip startup when their binary or generated config is
missing. Walker starts after its Elephant provider. Repeating the session action
uses `systemctl start`, leaving active services running. These units are started
by the session action, not enabled against `default.target`.

Waybar reloads its main process with SIGUSR2 through ExecReload. SwayNC reloads
config and CSS over its native client API. Walker and SwayOSD use targeted user
service refreshes; inactive services remain stopped. Theme refresh and global
`dotfiles reload` never activate or restart portals.

`dotfiles action portal` imports the same environment and idempotently starts the
portal frontend. Backends are D-Bus activated according to `portals.conf`: Hyprland
handles ScreenCast/Screenshot and GTK handles FileChooser. No portal process is
killed, restarted or spawned directly. Existing sharing sessions remain owned by
the running portal process; this action does not forcibly repair a stale backend.

## Migration and recovery

Review/stow the new `home/` files and run `dotfiles configure` to produce CSS.
Log out of the old session before testing the new login so legacy manually started
processes cannot coexist with the user units. Remove duplicate launches from any
personal autostart and previously enabled vendor units that you own. Do not run
two graphical sessions as the same user: user systemd and activation environment
are shared. UWSM remains optional and requires its own greetd validation.

From a TTY, inspect without changing state:

```sh
systemctl --user status hyprland-session.target graphical-session.target
systemctl --user status 'shade-raid-*.service' xdg-desktop-portal.service
journalctl --user -b -u 'shade-raid-*.service' -u xdg-desktop-portal.service
systemctl --user show-environment
```

If the native target is absent or login fails, restore the previous checkout's
autostart/unit files from a TTY, run `dotfiles link`, and log in again. Avoid
starting desktop units in the TTY's environment. Existing greetd recovery remains
documented in `recovery.md`.

## Required live smoke tests (not covered by container CI)

1. Keep a TTY open. Log in through greetd; check both session targets active and
   exactly one process per managed application. Check the journal for start loops.
2. Run `dotfiles action session` twice. Confirm each active unit's MainPID stays
   unchanged. Confirm user systemd has the current WAYLAND_DISPLAY and desktop.
3. Open a portal-backed file picker, choose/cancel a file, then screen-share from
   the browser and Vesktop. Verify the monitor selection and capture work.
4. While sharing, toggle light/dark. Portal MainPIDs and the sharing stream must
   survive. Check Waybar, Walker, notifications and OSD colors. Reapply the same
   theme and confirm no application refresh occurs.
5. Log out; check all Shade Raid units stop with graphical-session.target. Log in
   again and confirm no duplicate processes or stale display environment.

## Upstream references checked 2026-11-02

- [Hyprland systemd lifecycle](https://wiki.hypr.land/configuring/extra/systemd/)
- [Native session target](https://github.com/hyprwm/Hyprland/blob/main/systemd/hyprland-session.target)
- [systemd graphical session units](https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html#graphical-session.target)
- [Portal activation environment](https://flatpak.github.io/xdg-desktop-portal/docs/system-integration.html)
- [Portal backend selection](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html)
