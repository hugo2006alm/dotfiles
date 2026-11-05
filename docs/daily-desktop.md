# Daily desktop actions

Browser notifications are visible again. SwayNC no longer globally ignores Zen,
Firefox, Chrome or Spotify, and its MPRIS widget can show browser playback. Media
actions inspect available MPRIS players, prefer a currently playing one, and fall
back to an available paused/stopped player. The Pause key pauses; Play toggles.

Volume and brightness keys apply exactly one change: SwayOSD when its managed
service is active, otherwise wpctl/brightnessctl. The old double volume/mute change is removed.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| Super+H/J/K/L | Focus windows (no launcher/lock conflicts) |
| Super+Ctrl+L | Lock session |
| Super+Alt+H | Heroic, with an installation diagnostic if absent |
| Super+B | First installed browser: Zen, Firefox, Chromium, Chrome or Brave |
| Super+Alt+G | ChatGPT at https://chatgpt.com/ in that browser |
| Super+V | Elephant/Walker clipboard history |
| Super+Alt+V | Edit current text clipboard in Neovim inside Ghostty |
| Print / Shift+Print | Full/region screenshot; cancel creates no files |
| Super+Shift+R | Start/stop the managed recorder |
| Super+Shift+T | Toggle theme, with success/error feedback |

Optional Spotify, Steam, Heroic and Antigravity shortcuts use catalog launch
commands with executable checks and visible missing-package diagnostics. They
never invoke a shell with application arguments. Browser MIME associations point
to a stable Shade Raid desktop entry rather than an absent optional browser.
The launcher has a separate ChatGPT desktop entry. Codex's unofficial package is
correctly labelled as Codex, rather than ChatGPT.

Elephant's clipboard provider owns history storage for text/images; the duplicate
cliphist watcher is removed. The editor accepts plain-text MIME and uses an
anonymous Linux memory file with mode 0600. It runs Neovim without user config/plugins or ShaDa and disables swap, backup and
undo files; the buffer disappears when its last descriptor closes, including when
the action is killed. Clipboard content is not recorded in command logs. The
history provider may still persist entries separately; review its configuration.
Actual Neovim/Ghostty interoperability requires the live smoke test below.

Screenshots use unique filenames and pass paths with spaces as separate arguments.
Capture failure prevents clipboard/success notification. Recorder state includes
the owned process's UID and start time, so reused/stale PIDs cannot stop unrelated
processes. Startup errors are reported from a private runtime log, and a failure
to save recorder state terminates its child. Startup waits for a nonempty output, while stop uses a pidfd and waits for
process exit before asking the user to verify the output. A nonempty file is not
proof of a playable recording. Existing manually started
recorders are not killed. Dry-run creates no capture files or processes.

One foreground SSH agent runs in `shade-raid-ssh-agent.service`, with a private
runtime socket shared by compositor children and Fish. An agent supplied by the
session manager is preserved. Shell startup no longer spawns agents or silently
loads a hard-coded key. Load your selected key yourself using `ssh-add` in a
terminal. An agent is scoped to the graphical session, not every shell.

Floating application sizes use monitor-relative expressions, following current
Hyprland Lua rules, instead of fixed dimensions. Monitor-aware drawer generation
continues to use the actual logical monitor size.

## Live smoke matrix — all still pending

| Area | Manual check in Hyprland | Expected result |
| --- | --- | --- |
| Notifications | Send a browser notification and `notify-send test` | Both visible, with usable actions |
| Media | Pause Spotify, play a browser video, press media keys | Browser receives control; Pause never resumes |
| Controls | Press volume, mute and brightness keys once | One change, appropriate OSD, no double toggle |
| Bindings | Exercise H/L focus, new lock and Heroic keys | No conflicts; absent optional app explains requirement |
| Browser/MIME | Open an HTTPS link and an HTML file via xdg-open | Installed browser opens; no recursive launcher |
| ChatGPT | Launch ChatGPT from Walker and shortcut | Browser opens the official site |
| Clipboard | Copy text/image, reopen Walker, restart Elephant | History works and follows provider persistence |
| Clipboard editor | Edit text, save/exit, paste; cancel editor | Intended text copied; private file cleaned up |
| Windows | Open floating apps on different scales/monitors | Useful bounds inside current monitor |
| Screenshots | Full/region capture, cancel, Pictures path with spaces | Saved/copied correctly; cancellation creates nothing |
| Recording | Start/stop, inspect playable output; simulate failed start | Useful error; no unrelated PID signalled |
| SSH | Open three terminals and compare SSH_AUTH_SOCK/agent PID | One session agent; no shell-start key prompts |
| Theme | Toggle during sharing, repeat same theme, inject an error | Useful feedback; unchanged theme skips refresh; portals survive |

Automated tests cover action command selection, failure handling, private state,
binding conflicts and dry-run. They do not establish the live results above.

References checked 2026-11-03: [MPRIS controls](https://github.com/altdesktop/playerctl),
[Elephant clipboard](https://github.com/abenz1267/elephant/tree/master/internal/providers/clipboard),
[Hyprland size expressions](https://wiki.hypr.land/configuring/core/rules/window-rules/#position-and-size).
