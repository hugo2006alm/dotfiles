#!/bin/bash
# toggle-record.sh — toggle wf-recorder screen capture
# Super+Shift+R via keybinds.lua

SAVE_DIR="$(xdg-user-dir VIDEOS)/Recordings"
PID_FILE="/tmp/wf-recorder.pid"
mkdir -p "$SAVE_DIR"

# Check if wf-recorder is installed
if ! command -v wf-recorder &>/dev/null; then
    notify-send -u critical "Screen Recording" "wf-recorder is not installed.\nInstall with: yay -S wf-recorder"
    exit 1
fi

# Check via PID file (more reliable than pgrep across environments)
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    # Recording in progress — stop it
    kill -INT "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
    pkill -RTMIN+9 waybar 2>/dev/null || true
    notify-send -i media-record "Screen Recording" "Recording stopped and saved to $SAVE_DIR"
else
    rm -f "$PID_FILE"
    FILE="$SAVE_DIR/$(date +%Y%m%d_%H%M%S).mkv"
    wf-recorder -f "$FILE" &
    echo $! > "$PID_FILE"
    pkill -RTMIN+9 waybar 2>/dev/null || true
    notify-send -i media-record "Screen Recording" "Recording started…"
fi
