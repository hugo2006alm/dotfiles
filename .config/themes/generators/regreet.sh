#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get() { grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

echo "Generating ReGreet Theme..."
mkdir -p ~/.config/greetd

# Determine if this is a dark variant
IS_DARK=false
[[ "$THEME" == *"-dark"* ]] && IS_DARK=true

# Pull colors
BG=$(get background)
BG2=$(get background2)
FG=$(get foreground)
FG2=$(get foreground2)
ACCENT=$(get accent)
ACCENT_FG=$(get accent_fg)
INACTIVE=$(get inactive)

# For dark themes: invert the card to dark-on-blurred-background
if $IS_DARK; then
    CARD_BG="rgba(13, 13, 13, 0.78)"
    CARD_BORDER="rgba(217, 79, 43, 0.40)"
    CARD_FG="#F4EFE4"
    CARD_FG2="#C8C2B4"
    ENTRY_BG="rgba(13, 13, 13, 0.55)"
    BTN_BG="rgba(217, 79, 43, 0.0)"
    BTN_HOVER_BG="$ACCENT"
    BTN_HOVER_FG="$ACCENT_FG"
    SHADOW="rgba(0,0,0,0.6)"
else
    CARD_BG="rgba(244, 239, 228, 0.84)"
    CARD_BORDER="rgba(217, 79, 43, 0.35)"
    CARD_FG="#0D0D0D"
    CARD_FG2="#3A3A3A"
    ENTRY_BG="rgba(244, 239, 228, 0.5)"
    BTN_BG="rgba(217, 79, 43, 0.0)"
    BTN_HOVER_BG="$ACCENT"
    BTN_HOVER_FG="$ACCENT_FG"
    SHADOW="rgba(0,0,0,0.25)"
fi

cat <<CSS_EOF > ~/.config/greetd/regreet.css
/* ── Shade Raid — ReGreet Login Theme ── */
/* Generated from: $THEME */

@keyframes card-appear {
    from {
        opacity: 0;
        transform: translateY(12px) scale(0.98);
        filter: blur(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0px);
    }
}

@keyframes unblur-bg {
    from { filter: blur(30px) brightness(0.6); }
    to   { filter: blur(0px)  brightness(1.0); }
}

/* ── Root window ── */
window {
    background-color: transparent;
    /* The blurred wallpaper is set via regreet.toml; we let it show through */
    animation: unblur-bg 1.2s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* ── Login card ── */
.login-box {
    background-color: ${CARD_BG};
    border: 3px solid ${ACCENT};
    border-radius: 4px;
    padding: 40px 48px;
    min-width: 380px;
    box-shadow: 0 24px 64px ${SHADOW}, 0 2px 8px ${SHADOW};
    animation: card-appear 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* ── Typography ── */
* {
    font-family: "SpaceMono Nerd Font", "Space Mono", monospace;
    color: ${CARD_FG};
}

label {
    color: ${CARD_FG};
    font-size: 13px;
    letter-spacing: 0.04em;
}

/* Username / session labels */
label.subtitle,
label:not(.title) {
    color: ${CARD_FG2};
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Text entries (username, password) ── */
entry {
    background-color: ${ENTRY_BG};
    color: ${CARD_FG};
    border: none;
    border-bottom: 2px solid ${CARD_BORDER};
    border-radius: 2px 2px 0 0;
    padding: 10px 12px;
    font-family: "SpaceMono Nerd Font", "Space Mono", monospace;
    font-size: 13px;
    letter-spacing: 0.04em;
    transition: border-color 200ms ease, background-color 200ms ease;
}

entry:focus {
    border-bottom-color: ${ACCENT};
    background-color: ${ENTRY_BG};
    outline: none;
}

entry placeholder {
    color: ${CARD_FG2};
    opacity: 0.6;
}

/* ── Buttons ── */
button {
    background-color: transparent;
    color: ${CARD_FG};
    border: 1px solid ${CARD_BORDER};
    border-radius: 2px;
    padding: 8px 20px;
    font-family: "SpaceMono Nerd Font", "Space Mono", monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    transition: background-color 180ms ease, color 180ms ease, border-color 180ms ease;
}

button:hover {
    background-color: ${BTN_HOVER_BG};
    color: ${BTN_HOVER_FG};
    border-color: ${ACCENT};
}

button:active {
    background-color: ${ACCENT};
    color: ${BTN_HOVER_FG};
}

/* Primary login button — filled accent */
button.suggested-action,
button#login,
button#submit,
button.accent,
button.login,
button.submit,
.login button,
.submit button {
    background-color: ${ACCENT} !important;
    color: ${ACCENT_FG} !important;
    border-color: ${ACCENT} !important;
}

button.suggested-action:hover,
button#login:hover,
button#submit:hover,
button.accent:hover,
button.login:hover,
button.submit:hover,
.login button:hover,
.submit button:hover {
    background-color: ${BTN_HOVER_BG} !important;
    color: ${BTN_HOVER_FG} !important;
    border-color: ${ACCENT} !important;
    filter: brightness(1.08);
}

/* Power management buttons */
button.reboot, button#reboot,
button.poweroff, button#poweroff,
button.shutdown, button#shutdown,
button.suspend, button#suspend,
#reboot button, #poweroff button,
#shutdown button, #suspend button {
    background-color: transparent !important;
    color: ${CARD_FG} !important;
    border: 1px solid ${CARD_BORDER} !important;
}

button.reboot:hover, button#reboot:hover,
button.poweroff:hover, button#poweroff:hover,
button.shutdown:hover, button#shutdown:hover,
button.suspend:hover, button#suspend:hover,
#reboot button:hover, #poweroff button:hover,
#shutdown button:hover, #suspend button:hover {
    background-color: ${BTN_HOVER_BG} !important;
    color: ${BTN_HOVER_FG} !important;
    border-color: ${ACCENT} !important;
}

/* ── Dropdowns (session selector) ── */
comboboxtext,
combobox {
    background-color: ${ENTRY_BG};
    color: ${CARD_FG};
    border: 1px solid ${CARD_BORDER};
    border-radius: 2px;
    padding: 6px 10px;
    font-family: "SpaceMono Nerd Font", "Space Mono", monospace;
    font-size: 12px;
}

comboboxtext:hover,
combobox:hover {
    border-color: ${ACCENT};
}

/* Dropdown popover */
.popup {
    background-color: #1A1512;
    border: 1px solid ${CARD_BORDER};
    border-radius: 2px;
}

/* ── Error messages ── */
label.error {
    color: ${ACCENT};
    font-size: 11px;
    font-weight: 700;
}

/* ── Scrollbars (minimal) ── */
scrollbar {
    background-color: transparent;
    min-width: 4px;
    min-height: 4px;
}

scrollbar slider {
    background-color: ${CARD_FG2};
    border-radius: 2px;
    min-width: 4px;
    min-height: 20px;
}
CSS_EOF

# Copy CSS to /etc/greetd (requires write access or sudoers)
cp ~/.config/greetd/regreet.css /etc/greetd/regreet.css 2>/dev/null || true
# Also copy hyprland-greet config
cp ~/.config/greetd/hyprland-greet.conf /etc/greetd/hyprland-greet.conf 2>/dev/null || true

echo "ReGreet theme done — $THEME"
