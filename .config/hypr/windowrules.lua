-- Window Rules Configuration - Lua format for Hyprland 0.55+

-- Float rules
hl.window_rule({ match = { class = "xdg-desktop-portal" }, float = true })
hl.window_rule({ match = { class = "xdg-desktop-portal-hyprland" }, float = true })
hl.window_rule({ match = { title = "Open File" }, float = true })
hl.window_rule({ match = { title = "Save File" }, float = true })
hl.window_rule({ match = { title = "Select Install Path" }, float = true })
hl.window_rule({ match = { class = "Bitwarden" }, float = true })
hl.window_rule({ match = { class = "org.pulseaudio.pavucontrol" }, float = true })
hl.window_rule({ match = { class = "org.gnome.Nautilus" }, float = true })
hl.window_rule({ match = { class = "imv" }, float = true })
hl.window_rule({ match = { class = "mpv" }, float = true })
hl.window_rule({ match = { title = "btop" }, float = true })
hl.window_rule({ match = { title = "nmtui" }, float = true })
hl.window_rule({ match = { title = "bluetui" }, float = true })
hl.window_rule({ match = { class = "zen", title = "^Extensão:" }, float = true })
hl.window_rule({ match = { title = "System Update" }, float = true })

-- Size rules
hl.window_rule({ match = { class = "org.gnome.Nautilus" }, size = { 900, 600 } })
hl.window_rule({ match = { class = "org.pulseaudio.pavucontrol" }, size = { 800, 600 } })
hl.window_rule({ match = { class = "Bitwarden" }, size = { 1000, 700 } })
hl.window_rule({ match = { title = "btop" }, size = { 1200, 800 } })
hl.window_rule({ match = { title = "System Update" }, size = { 800, 500 } })

-- Workspace rules
hl.window_rule({ match = { class = "zen" }, workspace = "1" })
hl.window_rule({ match = { class = "com.mitchellh.ghostty" }, workspace = "2" })
hl.window_rule({ match = { class = "vesktop" }, workspace = "3" })
hl.window_rule({ match = { class = "antigravity" }, workspace = "4" })
hl.window_rule({ match = { class = "antigravity-ide" }, workspace = "5" })
hl.window_rule({ match = { class = "Hermes" }, workspace = "6" })
hl.window_rule({ match = { class = "Spotify" }, workspace = "9" })
hl.window_rule({ match = { class = "steam" }, workspace = "10" })
hl.window_rule({ match = { class = "heroic" }, workspace = "10" })
hl.window_rule({ match = { title = "Overwatch" }, workspace = "10" })

-- Special workspace assignments for drawers
hl.window_rule({ match = { title = "btop" }, workspace = "special:btop" })
hl.window_rule({ match = { title = "nmtui" }, workspace = "special:nmtui" })
hl.window_rule({ match = { title = "bluetui" }, workspace = "special:bluetui" })
hl.window_rule({ match = { class = "org.pulseaudio.pavucontrol" }, workspace = "special:pavucontrol" })

-- Opacity rules (dynamic effects)
hl.window_rule({ match = { class = "com.mitchellh.ghostty" }, opacity = "1.0 override" })
hl.window_rule({ match = { class = "antigravity" }, opacity = "0.92 override" })
hl.window_rule({ match = { class = "antigravity-ide" }, opacity = "0.92 override" })
hl.window_rule({ match = { class = "zen" }, opacity = "1.0 override 1.0 override" })
hl.window_rule({ match = { class = "vesktop" }, opacity = "0.95 override" })
hl.window_rule({ match = { class = "Bitwarden" }, opacity = "1.0 override" })

-- Suppress maximize
hl.window_rule({ match = { class = "steam" }, suppress_event = "maximize" })
hl.window_rule({ match = { class = "heroic" }, suppress_event = "maximize" })
hl.window_rule({ match = { class = "vesktop" }, suppress_event = "maximize" })

-- No initial focus
hl.window_rule({ match = { class = "vesktop" }, no_initial_focus = true })
hl.window_rule({ match = { class = "steam" }, no_initial_focus = true })

-- Idle inhibit rules
hl.window_rule({ match = { class = "mpv" }, idle_inhibit = "focus" })
hl.window_rule({ match = { class = "zen" }, idle_inhibit = "fullscreen" })

