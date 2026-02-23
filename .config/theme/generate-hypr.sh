#!/bin/bash

TOML=~/.config/theme/colors.toml

parse() {
  grep "^$1" "$TOML" | sed 's/.*= *"#\?//' | tr -d '"'
}

cat > ~/.config/hypr/colors.conf <<EOF
\$background  = rgb($(parse background\ ))
\$background2 = rgb($(parse background2))
\$foreground  = rgb($(parse foreground\ ))
\$foreground2 = rgb($(parse foreground2))
\$border      = rgb($(parse border))
\$accent      = rgb($(parse accent\ ))
\$accent2     = rgb($(parse accent2))
\$active      = rgb($(parse active))
\$inactive    = rgb($(parse inactive))
\$urgent      = rgb($(parse urgent))
\$shadow      = rgb($(parse shadow\ ))
EOF

echo "~/.config/hypr/colors.conf generated"
