import os
import subprocess
import shutil
from pathlib import Path
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class GreetdGenerator(BaseGenerator):
    def __init__(self, name: str = "greetd", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        is_dark = "dark" in theme_name
        is_dark_str = "true" if is_dark else "false"
        bg_file = "/etc/greetd/regreet-background.jpg"

        content = f"""[background]
path = "{bg_file}"
fit = "Cover"

[GTK]
application_prefer_dark_theme = {is_dark_str}
"""

        # Perform the blurred wallpaper generation if writable
        if self.transaction and self.transaction._env:
            target_bg = Path(bg_file)
            target_dir = target_bg.parent
            is_writable = False
            try:
                if target_bg.exists() and os.access(target_bg, os.W_OK):
                    is_writable = True
                elif not target_bg.exists() and target_dir.exists() and os.access(target_dir, os.W_OK):
                    is_writable = True
            except Exception:
                pass

            if is_writable:
                cache_wp = self.transaction._env.home_dir / ".cache" / "shade-raid" / "last_wallpaper"
                src_wall = None
                if cache_wp.exists():
                    try:
                        src_wall = cache_wp.read_text().strip()
                    except Exception:
                        pass
                
                if not src_wall or not Path(src_wall).exists():
                    base_theme = theme_name.split("-")[0]
                    wp_dir = self.transaction._env.home_dir / "wallpapers" / theme_name
                    if not wp_dir.exists():
                        wp_dir = self.transaction._env.home_dir / "wallpapers" / base_theme
                    if wp_dir.exists():
                        import glob
                        imgs = glob.glob(str(wp_dir / "*.jpg")) + glob.glob(str(wp_dir / "*.png"))
                        if imgs:
                            src_wall = imgs[0]
                
                if src_wall and Path(src_wall).exists() and shutil.which("convert"):
                    try:
                        subprocess.run([
                            "convert", str(Path(src_wall).resolve()),
                            "-filter", "Gaussian",
                            "-blur", "0x20",
                            "-modulate", "70",
                            str(target_bg)
                        ], capture_output=True, check=False)
                    except Exception:
                        try:
                            shutil.copy(str(Path(src_wall).resolve()), str(target_bg))
                        except Exception:
                            pass

        return [
            GeneratedArtifact(artifact_id="greetd-config", content=content)
        ]
