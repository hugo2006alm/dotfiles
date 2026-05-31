#!/bin/bash
set -e

if ! command -v spotify &> /dev/null; then
    echo "Spotify not installed, skipping Spicetify"
    exit 0
fi

if ! command -v spicetify &> /dev/null; then
    echo "Spicetify CLI not installed, skipping Spicetify"
    exit 0
fi

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"
SPICETIFY_CONFIG="$CONFIG_DIR/spicetify/config-xpui.ini"
SPOTIFY_PATH="/opt/spotify"
PREFS_PATH="$CONFIG_DIR/spotify/prefs"

if [[ -f "$SPICETIFY_CONFIG" ]]; then
    SPOTIFY_PATH=$(sed -n 's/^spotify_path[[:space:]]*=[[:space:]]*//p' "$SPICETIFY_CONFIG" | head -n 1 | xargs)
    PREFS_PATH=$(sed -n 's/^prefs_path[[:space:]]*=[[:space:]]*//p' "$SPICETIFY_CONFIG" | head -n 1 | xargs)
    SPOTIFY_PATH=${SPOTIFY_PATH:-/opt/spotify}
    PREFS_PATH=${PREFS_PATH:-$CONFIG_DIR/spotify/prefs}
fi

if [[ ! -f "$PREFS_PATH" ]]; then
    echo "Spotify prefs not found at $PREFS_PATH."
    echo "Launch Spotify once, then re-run extras.sh."
    exit 0
fi

if [[ ! -d "$SPOTIFY_PATH" ]]; then
    echo "Spotify path not found at $SPOTIFY_PATH, skipping Spicetify"
    exit 0
fi

echo "==> Spicetify setup..."
sudo chmod a+wr "$SPOTIFY_PATH"
sudo chmod -R a+wr "$SPOTIFY_PATH/Apps"
spicetify backup apply
curl -fsSL https://raw.githubusercontent.com/spicetify/marketplace/main/resources/install.sh | bash
spicetify refresh -a -e
spicetify apply
