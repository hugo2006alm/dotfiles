#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get() { grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

# Extract hex colors
BG_HEX=$(get background | sed 's/#//')
FG_HEX=$(get foreground | sed 's/#//')
ACCENT_HEX=$(get accent | sed 's/#//')

# Convert hex to float (0.0-1.0)
hex_to_rgb_float() {
  local hex=$1
  local r=$((16#${hex:0:2}))
  local g=$((16#${hex:2:2}))
  local b=$((16#${hex:4:2}))
  awk "BEGIN {printf \"%.3f, %.3f, %.3f\", $r/255, $g/255, $b/255}"
}

BG_FLOAT=$(hex_to_rgb_float "$BG_HEX")
FG_FLOAT=$(hex_to_rgb_float "$FG_HEX")
ACCENT_FLOAT=$(hex_to_rgb_float "$ACCENT_HEX")

echo "Generating Plymouth Theme..."

cat << SCRIPT_EOF > ~/dotfiles/plymouth-shade-raid/shade-raid.script
// Background: #$BG_HEX
Window.SetBackgroundTopColor($BG_FLOAT);
Window.SetBackgroundBottomColor($BG_FLOAT);

// Text styling: Foreground #$FG_HEX
// Accent styling: #$ACCENT_HEX

// Hard geometric text
box_image = Image.Text("SHADE RAID", $FG_FLOAT, 1, "Monospace 36");
box_sprite = Sprite(box_image);
box_sprite.SetX(Window.GetWidth() / 2 - box_image.GetWidth() / 2);
box_sprite.SetY(Window.GetHeight() / 2 - box_image.GetHeight() / 2);

// Simple dot progress
max_progress_text = Image.Text("....", $ACCENT_FLOAT, 1, "Monospace 36");
progress_text = Image.Text(".", $ACCENT_FLOAT, 1, "Monospace 36");
progress_sprite = Sprite(progress_text);
progress_sprite.SetX(Window.GetWidth() / 2 - max_progress_text.GetWidth() / 2);
progress_sprite.SetY(Window.GetHeight() / 2 + box_image.GetHeight());

progress = 0;

fun refresh_callback () {
    progress++;
    if (progress % 100 < 25) {
        progress_text = Image.Text(".", $ACCENT_FLOAT, 1, "Monospace 36");
    } else if (progress % 100 < 50) {
        progress_text = Image.Text("..", $ACCENT_FLOAT, 1, "Monospace 36");
    } else if (progress % 100 < 75) {
        progress_text = Image.Text("...", $ACCENT_FLOAT, 1, "Monospace 36");
    } else {
        progress_text = Image.Text("....", $ACCENT_FLOAT, 1, "Monospace 36");
    }
    progress_sprite.SetImage(progress_text);
}

Plymouth.SetRefreshFunction(refresh_callback);
SCRIPT_EOF
