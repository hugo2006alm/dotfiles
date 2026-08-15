PACKAGE_SOURCES: dict[str, str] = {
    # AUR packages used by the base desktop profile
    "walker-bin": "yay",
    "elephant-all": "yay",
    "wlogout": "yay",
    "bibata-cursor-theme": "yay",
    "papirus-folders": "yay",
    "vesktop-bin": "yay",
    "heroic-games-launcher-bin": "yay",
    "spotify": "yay",
    "spicetify-cli": "yay",
    "zen-browser-bin": "yay",
    "otf-bebas-neue": "yay",

    # Optional AUR packages
    "android-studio": "yay",
    "android-apktool-bin": "yay",
    "antigravity": "yay",
    "antigravity-ide": "yay",
    "codex-desktop": "yay",
    "neofetch": "yay",
    "phinger-cursors": "yay",
}


OPTIONAL_PACKAGES: list[dict[str, object]] = [
    # Android / mobile development
    {"package": "android-tools", "label": "Android platform tools (adb/fastboot)", "category": "Android", "source": "pacman"},
    {"package": "android-studio", "label": "Android Studio", "category": "Android", "source": "yay"},
    {"package": "android-apktool-bin", "label": "APKTool", "category": "Android", "source": "yay"},

    # Development
    {"package": "docker", "label": "Docker Engine", "category": "Development", "source": "pacman"},
    {"package": "uv", "label": "uv Python package/project manager", "category": "Development", "source": "pacman"},
    {"package": "plantuml", "label": "PlantUML", "category": "Development", "source": "pacman"},
    {"package": "codex-desktop", "label": "Codex Desktop", "category": "Development", "source": "yay"},
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

    # Gaming extras
    {"package": "protontricks", "label": "Protontricks", "category": "Gaming", "source": "pacman"},

    # Utilities / appearance currently used on this setup
    {"package": "dmidecode", "label": "dmidecode", "category": "Utilities", "source": "pacman"},
    {"package": "rsync", "label": "rsync", "category": "Utilities", "source": "pacman"},
    {"package": "wget", "label": "wget", "category": "Utilities", "source": "pacman"},
    {"package": "neofetch", "label": "Neofetch (legacy)", "category": "Utilities", "source": "yay"},
    {"package": "capitaine-cursors", "label": "Capitaine cursors", "category": "Appearance", "source": "pacman"},
    {"package": "phinger-cursors", "label": "Phinger cursors", "category": "Appearance", "source": "yay"},
]
