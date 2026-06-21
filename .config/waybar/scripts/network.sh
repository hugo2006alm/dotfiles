#!/bin/bash
# Waybar custom network module — shows primary connection + all interfaces in tooltip

# Primary interface (default route)
IFACE=$(ip route show default 2>/dev/null | awk 'NR==1{print $5}')

# Determine label
if [ -z "$IFACE" ]; then
    LABEL="NO NET"
elif echo "$IFACE" | grep -qi "wl"; then
    SIGNAL=$(awk 'NR==3{printf "%.0f", ($3/70)*100}' /proc/net/wireless 2>/dev/null)
    LABEL="WiFi ${SIGNAL}%"
else
    LABEL="ETH"
fi

# Build tooltip — list every interface with an IPv4 address (excluding loopback)
TOOLTIP=""
while read -r line; do
    iface=$(echo "$line" | awk '{print $1}' | tr -d ':')
    ip_addr=$(echo "$line" | awk '{print $2}')
    TOOLTIP+="$iface  $ip_addr\\n"
done < <(ip addr show | awk '/^[0-9]+:/{iface=$2} /inet /{print iface" "$2}' | grep -v "^lo")

# Remove trailing newline
TOOLTIP="${TOOLTIP%\\n}"

# Output JSON for waybar
printf '{"text": "%s", "tooltip": "%s"}\n' "$LABEL" "$TOOLTIP"
