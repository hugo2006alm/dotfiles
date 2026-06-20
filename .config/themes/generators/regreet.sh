#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get() { grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

echo "Generating ReGreet Theme..."
mkdir -p ~/.config/greetd

cat <<CSS_EOF > ~/.config/greetd/regreet.css
window {
    background-color: $(get background);
    color: $(get foreground);
}
.login-box {
    background-color: $(get background2);
    border: 2px solid $(get accent);
    border-radius: 0;
    padding: 24px;
}
button {
    background-color: $(get background);
    color: $(get foreground);
    border: 1px solid $(get inactive);
    border-radius: 0;
}
button:hover, button:active {
    background-color: $(get accent);
    color: $(get accent_fg);
}
entry {
    background-color: $(get background);
    color: $(get foreground);
    border: 1px solid $(get inactive);
    border-radius: 0;
}
entry:focus {
    border-color: $(get accent);
}
CSS_EOF

# Copy CSS to /etc/greetd
cp ~/.config/greetd/regreet.css /etc/greetd/regreet.css 2>/dev/null || true
# Also copy hyprland-greet
cp ~/.config/greetd/hyprland-greet.conf /etc/greetd/hyprland-greet.conf 2>/dev/null || true
