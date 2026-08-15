PACKAGE_SOURCES: dict[str, str] = {
    # Official repo packages that used to be routed through yay in the CLI
    "hyprlock": "pacman",
    "hypridle": "pacman",
    "hyprsunset": "pacman",
    "hyprpicker": "pacman",
    "hyprshot": "pacman",
    "greetd": "pacman",
    "greetd-regreet": "pacman",
    "bluetui": "pacman",
    "bitwarden": "pacman",
    "ttf-iosevka-nerd": "pacman",

    # AUR packages used by the base desktop profile
    "walker-bin": "yay",
    "elephant-all": "yay",
    "wlogout": "yay",
    "bibata-cursor-theme": "yay",
    "papirus-folders": "yay",
    "otf-bebas-neue-git": "yay",

    # Optional AUR packages
    "android-studio": "yay",
    "android-apktool-bin": "yay",
    "antigravity": "yay",
    "antigravity-ide": "yay",
    "codex-app-unofficial": "yay",
    "heroic-games-launcher-bin": "yay",
    "neofetch": "yay",
    "phinger-cursors": "yay",
    "spotify": "yay",
    "spicetify-cli": "yay",
    "vesktop-bin": "yay",
    "zen-browser-bin": "yay",
}


OPTIONAL_PACKAGES: list[dict[str, object]] = [
    # Personal desktop apps
    {"package": "codex-app-unofficial", "label": "ChatGPT Desktop (unofficial Linux build)", "category": "Apps", "source": "yay"},
    {"package": "spotify", "label": "Spotify", "category": "Apps", "source": "yay"},
    {"package": "spicetify-cli", "label": "Spicetify CLI (Spotify customization)", "category": "Apps", "source": "yay"},
    {"package": "vesktop-bin", "label": "Vesktop (Discord client)", "category": "Apps", "source": "yay"},
    {"package": "bitwarden", "label": "Bitwarden", "category": "Apps", "source": "pacman"},
    {"package": "zen-browser-bin", "label": "Zen Browser", "category": "Apps", "source": "yay"},

    # Android / mobile development
    {"package": "android-tools", "label": "Android platform tools (adb/fastboot)", "category": "Android", "source": "pacman"},
    {"package": "android-studio", "label": "Android Studio", "category": "Android", "source": "yay"},
    {"package": "android-apktool-bin", "label": "APKTool", "category": "Android", "source": "yay"},

    # Development
    {"package": "docker", "label": "Docker Engine", "category": "Development", "source": "pacman"},
    {"package": "uv", "label": "uv Python package/project manager", "category": "Development", "source": "pacman"},
    {"package": "plantuml", "label": "PlantUML", "category": "Development", "source": "pacman"},
    {
        "package": "antigravity",
        "label": "Antigravity",
        "category": "Development",
        "source": "yay",
        "conflicts": ["antigravity-ide"],
    },
    {
        "package": "antigravity-ide",
        "label": "Antigravity IDE",
        "category": "Development",
        "source": "yay",
        "conflicts": ["antigravity"],
    },

    # Creative / media
    {"package": "inkscape", "label": "Inkscape", "category": "Creative", "source": "pacman"},
    {"package": "obs-studio", "label": "OBS Studio", "category": "Creative", "source": "pacman"},

    # AI / compute
    {"package": "ollama-rocm", "label": "Ollama with ROCm support", "category": "AI / Compute", "source": "pacman"},
    {"package": "rocm-hip-sdk", "label": "ROCm HIP SDK", "category": "AI / Compute", "source": "pacman"},
    {"package": "rocm-opencl-sdk", "label": "ROCm OpenCL SDK", "category": "AI / Compute", "source": "pacman"},

    # Networking / services
    {"package": "tailscale", "label": "Tailscale", "category": "Networking", "source": "pacman"},
    {"package": "nginx", "label": "nginx", "category": "Networking", "source": "pacman"},

    # Gaming apps / extras
    {"package": "steam", "label": "Steam", "category": "Gaming", "source": "pacman"},
    {"package": "heroic-games-launcher-bin", "label": "Heroic Games Launcher", "category": "Gaming", "source": "yay"},
    {"package": "protontricks", "label": "Protontricks", "category": "Gaming", "source": "pacman"},

    # Alternative desktop tools already installed on this setup
    {"package": "rofi", "label": "Rofi (alternative launcher)", "category": "Desktop alternatives", "source": "pacman"},
    {"package": "mako", "label": "Mako (alternative notification daemon)", "category": "Desktop alternatives", "source": "pacman"},
    {"package": "nano", "label": "Nano editor", "category": "Desktop alternatives", "source": "pacman"},

    # Utilities / appearance currently used on this setup
    {"package": "dmidecode", "label": "dmidecode", "category": "Utilities", "source": "pacman"},
    {"package": "rsync", "label": "rsync", "category": "Utilities", "source": "pacman"},
    {"package": "wget", "label": "wget", "category": "Utilities", "source": "pacman"},
    {"package": "neofetch", "label": "Neofetch (legacy)", "category": "Utilities", "source": "yay"},
    {"package": "capitaine-cursors", "label": "Capitaine cursors", "category": "Appearance", "source": "pacman"},
    {"package": "phinger-cursors", "label": "Phinger cursors", "category": "Appearance", "source": "yay"},
]
