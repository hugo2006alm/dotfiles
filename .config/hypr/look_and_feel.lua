-- Look and Feel Configuration
-- General, Decoration, Animations, Environment Variables

-- Load dynamically generated colors and style configs
local colors = dofile(os.getenv("HOME") .. "/.config/hypr/colors.lua")
local style = dofile(os.getenv("HOME") .. "/.config/hypr/style.lua")

-- Environment variables
hl.env("XCURSOR_THEME", style.cursor_theme)
hl.env("XCURSOR_SIZE", tostring(style.cursor_size))
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "wayland")
hl.env("WLR_DRM_NO_MODIFIERS", "1")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")


-- General settings
hl.config({
    general = {
        gaps_in      = style.gaps_inner,
        gaps_out     = style.gaps_outer,
        border_size  = style.border_size,
        col = {
            active_border   = colors.active,
            inactive_border = colors.inactive,
        },
        layout = "dwindle",
    },
    dwindle = {
        preserve_split = true,
    },
})

-- Decoration settings
hl.config({
    decoration = {
        rounding         = style.corner_radius,
        inactive_opacity = 0.92,
        blur = {
            enabled = false,
        },
        shadow = {
            enabled      = true,
            range        = style.shadow_range,
            offset       = { style.shadow_offset_x, style.shadow_offset_y },
            render_power = style.shadow_render_power,
            color        = colors.shadow,
        },
    },
})

-- Animation curves
hl.curve("linear",  { type = "bezier", points = { {0, 0}, {1, 1} } })
hl.curve("snappy",  { type = "bezier", points = { {0.25, 0}, {0.25, 1} } })

-- Animations
hl.config({
    animations = {
        enabled = true,
    },
})

hl.animation({ leaf = "windows",    enabled = true, speed = 3, bezier = "snappy", style = "slide" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 3, bezier = "snappy", style = "slide" })
hl.animation({ leaf = "fade",       enabled = true, speed = 3, bezier = "linear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "snappy", style = "slide" })

-- XWayland settings
hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})