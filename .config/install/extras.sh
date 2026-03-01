#!/bin/bash
set -e

if ! command -v spotify &> /dev/null; then
    echo "Spotify not installed, skipping Spicetify"
    exit 0
fi

echo "==> Spicetify setup..."
echo "  NOTE: Launch Spotify once manually, then re-run this step."
read -p "  Has Spotify been launched at least once? (y/N): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    sudo chmod a+wr /opt/spotify
    sudo chmod a+wr /opt/spotify/Apps -R
    spicetify backup apply
    curl -fsSL https://raw.githubusercontent.com/spicetify/marketplace/main/resources/install.sh | sh
    spicetify apply
else
    echo "  Skipping Spicetify — launch Spotify first, then run extras.sh manually."
fi
