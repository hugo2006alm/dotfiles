#!/bin/bash
# toggle-record.sh — toggle wf-recorder screen capture
# Super+Shift+R via keybinds.lua

SAVE_DIR="$HOME/Videos/Recordings"
mkdir -p "$SAVE_DIR"

if pgrep -x wf-recorder > /dev/null; then
    # Recording in progress — stop it
    pkill -INT wf-recorder
    notify-send -i media-record "Screen Recording" "Recording stopped and saved to $SAVE_DIR"
else
    # Start a new recording
    FILE="$SAVE_DIR/$(date +%Y%m%d_%H%M%S).mkv"
    wf-recorder -f "$FILE" &
    notify-send -i media-record "Screen Recording" "Recording started…"
fi
