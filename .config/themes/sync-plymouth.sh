#!/bin/bash
# Asynchronously called by generate.sh to sync Plymouth

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec 9>/tmp/plymouth_sync.lock
if ! flock -n 9; then
    # Another sync daemon is already running. It will pick up the pending flag.
    exit 0
fi

# Small debounce so rapid switching doesn't instantly trigger a build
sleep 2

while [ -f /tmp/plymouth_sync_pending ]; do
    rm -f /tmp/plymouth_sync_pending
    
    cp "$DIR/../../plymouth-shade-raid/"* /usr/share/plymouth/themes/shade-raid/
    plymouth-set-default-theme shade-raid
    nice -n 19 ionice -c 3 mkinitcpio -P
    
    # Wait a moment before checking the flag again
    sleep 2
done
