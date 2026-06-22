from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class PlymouthGenerator(BaseGenerator):
    def __init__(self, name: str = "plymouth", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#F4EFE4")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D")
        accent = tokens.colors.colors.get("accent", "#D94F2B")

        def hex_to_rgb_float(hex_str: str) -> str:
            hex_clean = hex_str.lstrip('#')
            if len(hex_clean) != 6:
                return "1.0, 1.0, 1.0"
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            return f"{r/255:.3f}, {g/255:.3f}, {b/255:.3f}"

        bg_float = hex_to_rgb_float(bg)
        fg_float = hex_to_rgb_float(fg)
        accent_float = hex_to_rgb_float(accent)

        content = f"""// Background: {bg}
Window.SetBackgroundTopColor({bg_float});
Window.SetBackgroundBottomColor({bg_float});

// Text styling: Foreground {fg}
// Accent styling: {accent}

// Hard geometric text
box_image = Image.Text("SHADE RAID", {fg_float}, 1, "Monospace 36");
box_sprite = Sprite(box_image);
box_sprite.SetX(Window.GetWidth() / 2 - box_image.GetWidth() / 2);
box_sprite.SetY(Window.GetHeight() / 2 - box_image.GetHeight() / 2);

// Simple dot progress
max_progress_text = Image.Text("....", {accent_float}, 1, "Monospace 36");
progress_text = Image.Text(".", {accent_float}, 1, "Monospace 36");
progress_sprite = Sprite(progress_text);
progress_sprite.SetX(Window.GetWidth() / 2 - max_progress_text.GetWidth() / 2);
progress_sprite.SetY(Window.GetHeight() / 2 + box_image.GetHeight());

progress = 0;

fun refresh_callback () {{
    progress++;
    if (progress % 100 < 25) {{
        progress_text = Image.Text(".", {accent_float}, 1, "Monospace 36");
    }} else if (progress % 100 < 50) {{
        progress_text = Image.Text("..", {accent_float}, 1, "Monospace 36");
    }} else if (progress % 100 < 75) {{
        progress_text = Image.Text("...", {accent_float}, 1, "Monospace 36");
    }} else {{
        progress_text = Image.Text("....", {accent_float}, 1, "Monospace 36");
    }}
    progress_sprite.SetImage(progress_text);
}}

Plymouth.SetRefreshFunction(refresh_callback);
"""
        return [
            GeneratedArtifact(artifact_id="plymouth-theme", content=content)
        ]
