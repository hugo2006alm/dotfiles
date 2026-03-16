# Hyprland Configuration Setup

## Changes to `.config/hypr/hyprland.conf`

### Added: XWayland force_zero_scaling configuration

Adds XWayland scaling configuration to prevent scaling issues with X11 applications under Wayland/Hyprland.

**File:** `.config/hypr/hyprland.conf`

**Configuration:**
```ini
xwayland {
    force_zero_scaling = true
}
```

**Purpose:**
- Fixes scaling issues for X11 applications running under XWayland
- Ensures X11 windows display correctly without double scaling
- Improves compatibility with legacy X11 applications in Wayland environment

**Location in Config:**
Added after environment variable definitions and before the `general` section.

**Related Files:**
- `.config/hypr/hyprland.conf` - Main Hyprland window manager configuration
- `.config/hypr/` - Hyprland configuration directory
