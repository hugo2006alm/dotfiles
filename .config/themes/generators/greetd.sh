#!/bin/bash

# Reads the global colors.toml and generates tuigreet arguments
# Writes to /etc/greetd/tuigreet-theme.args if writable

THEME="$1"
if [ -z "$THEME" ]; then
  exit 1
fi

TOML="$HOME/.config/themes/$THEME/colors.toml"

if [ ! -f "$TOML" ]; then
  exit 1
fi

# Simple TOML parser function
get_color() {
  grep -E "^$1\s*=" "$TOML" | cut -d'"' -f2
}

# Extract colors
bg=$(get_color "background")
fg=$(get_color "foreground")
accent=$(get_color "accent")
inactive=$(get_color "inactive")
border=$(get_color "border")
urgent=$(get_color "urgent")

# Ensure /etc/greetd/tuigreet-theme.args exists and is writable
ARGS_FILE="/etc/greetd/tuigreet-theme.args"

if [ -w "$ARGS_FILE" ]; then
  # tuigreet theme format:
  # --theme "border=COLOR;text=COLOR;prompt=COLOR;time=COLOR;action=COLOR;button=COLOR;container=COLOR;input=COLOR"
  # Colors must be hex or basic color names
  
  THEME_STR="border=$accent;text=$fg;prompt=$accent;time=$inactive;action=$accent;button=$accent;container=$bg;input=$fg"
  
  echo "--theme \"$THEME_STR\"" > "$ARGS_FILE"
fi
