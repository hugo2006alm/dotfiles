-- Look and Feel Configuration
-- General, Decoration, Animations, Environment Variables

-- Colors (from colors.conf)
local colors = {
    background    = 0x16130F,
    background2   = 0x201C17,
    foreground    = 0xF4EFE4,
    foreground2   = 0xC8C2B4,
    border        = 0xF4EFE4,
    accent        = 0xE8623E,
    accent2       = 0xD94F2B,
    active        = 0xF4EFE4,
    inactive      = 0x4A4540,
    urgent        = 0xE8623E,
    shadow        = 0x00000099,
}

-- Style variables (from style.conf)
local style = {
    border_size         = 3,
    gaps_inner          = 4,
    gaps_outer          = 8,
    corner_radius       = 0,
    cursor_theme        = "Bibata-Modern-Classic",
    cursor_size         = 24,
    font_mono           = "Monaspace Radon",
    font_display        = "Bebas Neue",
    font_size_sm        = 11,
    font_size_md        = 13,
    font_size_lg        = 24,
    shadow_offset_x     = 2,
    shadow_offset_y     = 2,
    shadow_range        = 4,
    shadow_render_power = 4,
}

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
        pseudotile = true,
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