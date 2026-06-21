#!/bin/bash
# Daemon to trigger SwayNC panel open when cursor is swiped left from the right edge

get_width() {
    local w=$(hyprctl monitors -j | jq '(.[] | select(.focused == true)) // .[0] | .width / .scale' 2>/dev/null | awk '{print int($1)}')
    if [ -z "$w" ] || [ "$w" -le 0 ]; then
        echo 1600
    else
        echo "$w"
    fi
}

MON_W=$(get_width)
LAST_CALC=$(date +%s)

while true; do
    sleep 0.08
    
    pos=$(hyprctl cursorpos 2>/dev/null)
    [ -z "$pos" ] && continue
    x=${pos%%,*}
    
    # If cursor gets near the cached edge, refresh MON_W dynamically for instant resolution-change handling
    if [ "$x" -ge $((MON_W - 10)) ]; then
        MON_W=$(get_width)
    fi
    
    # If cursor hits the right edge (within 2px)
    if [ "$x" -ge $((MON_W - 2)) ]; then
        # Right edge hit! Check for quick left swipe (within 240ms)
        for step in {1..8}; do
            sleep 0.03
            pos=$(hyprctl cursorpos 2>/dev/null)
            [ -z "$pos" ] && continue
            curr_x=${pos%%,*}
            
            # If they swiped left by 150px or more
            if [ "$curr_x" -le $((MON_W - 150)) ]; then
                swaync-client -t
                sleep 0.6 # Debounce to avoid multiple toggles
                break
            fi
        done
    fi
done
