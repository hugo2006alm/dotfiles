-- Keybindings Configuration - Lua format for Hyprland 0.55+

local terminal = "ghostty"
local launcher = "walker"
local browser = "zen-browser"

-- Helper function for keybinds
local function bind(keys, dispatcher, flags)
    hl.bind(keys, dispatcher, flags or {})
end

-- Application launchers
bind("SUPER + Return", hl.dsp.exec_cmd("GTK_IM_MODULE=simple " .. terminal))
bind("ALT + F4", hl.dsp.window.close())
bind("SUPER + Q", hl.dsp.window.close())
bind("SUPER + SHIFT + Q", hl.dsp.exit())
bind("SUPER + N", hl.dsp.exec_cmd("nautilus"))
bind("SUPER + SHIFT + E", hl.dsp.exec_cmd("walker --provider emojis"))
bind("SUPER + B", hl.dsp.exec_cmd(browser))
bind("SUPER + M", hl.dsp.exec_cmd("spotify"))
bind("SUPER + S", hl.dsp.exec_cmd("steam"))
bind("SUPER + H", hl.dsp.exec_cmd("heroic"))
bind("SUPER + A", hl.dsp.exec_cmd("antigravity"))
bind("SUPER + I", hl.dsp.exec_cmd("antigravity-ide"))
bind("SUPER + L", hl.dsp.exec_cmd("hyprlock"))

-- Launchers
bind("SUPER + Space", hl.dsp.exec_cmd(launcher))
bind("SUPER + ALT + Space", hl.dsp.exec_cmd(launcher))
bind("SUPER + R", hl.dsp.exec_cmd(launcher .. " --provider runner"))
bind("SUPER + C", hl.dsp.exec_cmd(launcher .. " --provider calculator"))

-- Fullscreen
bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
bind("ALT + Return", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
bind("SUPER + SHIFT + F", hl.dsp.window.fullscreen({ mode = "maximized", action = "toggle" }))

-- Window management
bind("SUPER + V", hl.dsp.exec_cmd(launcher .. " --provider clipboard"))
bind("SUPER + SHIFT + V", hl.dsp.window.float({ action = "toggle" }))
bind("SUPER + P", hl.dsp.window.pseudo({ action = "toggle" }))


-- Focus movement
bind("SUPER + left",  hl.dsp.focus({ direction = "l" }))
bind("SUPER + right", hl.dsp.focus({ direction = "r" }))
bind("SUPER + up",    hl.dsp.focus({ direction = "u" }))
bind("SUPER + down",  hl.dsp.focus({ direction = "d" }))

-- Vim-style focus movement
bind("SUPER + H", hl.dsp.focus({ direction = "l" }))
bind("SUPER + L", hl.dsp.focus({ direction = "r" }))
bind("SUPER + K", hl.dsp.focus({ direction = "u" }))
bind("SUPER + J", hl.dsp.focus({ direction = "d" }))

-- Move windows
bind("SUPER + SHIFT + left",  hl.dsp.window.move({ direction = "l" }))
bind("SUPER + SHIFT + right", hl.dsp.window.move({ direction = "r" }))
bind("SUPER + SHIFT + up",    hl.dsp.window.move({ direction = "u" }))
bind("SUPER + SHIFT + down",  hl.dsp.window.move({ direction = "d" }))

-- Resize windows (using relative coordinates)
bind("SUPER + CTRL + left",  hl.dsp.window.resize({ x = -40, y = 0, relative = true }))
bind("SUPER + CTRL + right", hl.dsp.window.resize({ x = 40, y = 0, relative = true }))
bind("SUPER + CTRL + up",    hl.dsp.window.resize({ x = 0, y = -40, relative = true }))
bind("SUPER + CTRL + down",  hl.dsp.window.resize({ x = 0, y = 40, relative = true }))

-- Workspace navigation (using focus with workspace)
bind("SUPER + ALT + right", hl.dsp.focus({ workspace = "e+1" }))
bind("SUPER + ALT + left",  hl.dsp.focus({ workspace = "e-1" }))

-- Direct workspace access (number row)
for i = 1, 10 do
    local key = tostring(i % 10)
    bind("SUPER + " .. key, hl.dsp.focus({ workspace = i }))
    bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- Keypad workspace access
local keypad_map = {
    KP_End   = 1, KP_Down  = 2, KP_Next   = 3,
    KP_Left  = 4, KP_Begin = 5, KP_Right  = 6,
    KP_Home  = 7, KP_Up    = 8, KP_Prior  = 9,
    KP_Insert = 10,
}
for kp_key, ws_num in pairs(keypad_map) do
    bind("SUPER + " .. kp_key, hl.dsp.focus({ workspace = ws_num }))
    bind("SUPER + SHIFT + " .. kp_key, hl.dsp.window.move({ workspace = ws_num }))
end

-- Screenshots
bind("Print", hl.dsp.exec_cmd([[bash -c 'f=$HOME/Imagens/Screenshots/$(date +%Y%m%d_%H%M%S).png; grim "$f" && wl-copy < "$f" && notify-send "Screenshot copied"']]))
bind("SHIFT + Print", hl.dsp.exec_cmd([[bash -c 'grim -g "$(slurp)" - | tee $HOME/Imagens/Screenshots/$(date +%Y%m%d_%H%M%S).png | wl-copy && notify-send "Screenshot copied"']]))
bind("SUPER + SHIFT + S", hl.dsp.exec_cmd([[bash -c 'grim -g "$(slurp)" - | tee $HOME/Imagens/Screenshots/$(date +%Y%m%d_%H%M%S).png | wl-copy && notify-send "Screenshot copied"']]))

-- Screen recording
bind("SUPER + SHIFT + R", hl.dsp.exec_cmd("$HOME/.config/hypr/scripts/toggle-record.sh"))

-- Media controls
bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"))
bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"))
bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"))
bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"))
bind("XF86AudioStop",  hl.dsp.exec_cmd("playerctl stop"))

-- Volume
bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+ && swayosd-client --output-volume raise"))
bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- && swayosd-client --output-volume lower"))
bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle && swayosd-client --output-volume mute-toggle"))

-- Brightness
bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl set 5%+ && swayosd-client --brightness raise"))
bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 5%- && swayosd-client --brightness lower"))

-- Mako notifications
bind("SUPER + D", hl.dsp.exec_cmd("makoctl dismiss"))
bind("SUPER + SHIFT + D", hl.dsp.exec_cmd("makoctl dismiss -a"))

-- Mouse bindings
bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Theme toggle
bind("SUPER + SHIFT + T", hl.dsp.exec_cmd("$HOME/.config/themes/toggle.sh"))

-- Wallpaper changer
bind("SUPER + SHIFT + W", hl.dsp.exec_cmd("$HOME/.config/hypr/scripts/wallpaper_changer.sh"))