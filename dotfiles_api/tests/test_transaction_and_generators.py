import unittest
import tempfile
import shutil
import json
from pathlib import Path
from dotfiles_api.domain.tokens import ColorTokens, MetricTokens, TypographyTokens, DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.infrastructure.generators.hypr import HyprlandGenerator
from dotfiles_api.infrastructure.generators.waybar import WaybarGenerator

class MockArtifactStore:
    def __init__(self, mappings):
        self.mappings = mappings

    def resolve_path(self, artifact_id: str, theme_name: str = "") -> Path:
        return self.mappings.get(artifact_id)

class MockFileWriter:
    def __init__(self):
        self.writes = {}

    def write(self, target_path: Path, content: str) -> None:
        self.writes[target_path] = content
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)

class TestConfigTransaction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env = EnvironmentContext(
            home_dir=Path(self.temp_dir),
            dotfiles_dir=Path(self.temp_dir) / "dotfiles",
            user="user"
        )
        self.file_a = Path(self.temp_dir) / "config_a.txt"
        self.file_b = Path(self.temp_dir) / "config_b.txt"

        self.file_a.write_text("original a")
        self.file_b.write_text("original b")

        self.store = MockArtifactStore({
            "art-a": self.file_a,
            "art-b": self.file_b
        })
        self.writer = MockFileWriter()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_successful_transaction_commits(self):
        # Act
        with ConfigTransaction(env=self.env, store=self.store, writer=self.writer) as tx:
            tx.write_artifact(GeneratedArtifact(artifact_id="art-a", content="new a"))
            tx.write_artifact(GeneratedArtifact(artifact_id="art-b", content="new b"))

        # Assert
        self.assertEqual(self.file_a.read_text(), "new a")
        self.assertEqual(self.file_b.read_text(), "new b")

    def test_failed_transaction_rolls_back(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            with ConfigTransaction(env=self.env, store=self.store, writer=self.writer) as tx:
                tx.write_artifact(GeneratedArtifact(artifact_id="art-a", content="new a"))
                raise ValueError("Oops, simulation failed!")

        # Assert files reverted
        self.assertEqual(self.file_a.read_text(), "original a")
        self.assertEqual(self.file_b.read_text(), "original b")

    def test_dry_run_transaction_does_not_write_but_logs(self):
        # Act
        with ConfigTransaction(env=self.env, store=self.store, writer=self.writer, dry_run=True) as tx:
            tx.write_artifact(GeneratedArtifact(artifact_id="art-a", content="new a"))

        # Assert files are NOT modified
        self.assertEqual(self.file_a.read_text(), "original a")

    def test_theme_name_interpolation_in_resolve_path(self):
        # Arrange
        file_tpl = Path(self.temp_dir) / "{theme_name}_config.txt"
        store_with_template = ArtifactStore({"templated": file_tpl})
        
        # Act
        with ConfigTransaction(env=self.env, store=store_with_template, writer=self.writer) as tx:
            tx.theme_name = "shade-raid"
            tx.write_artifact(GeneratedArtifact(artifact_id="templated", content="hello"))
            
        # Assert
        target = Path(self.temp_dir) / "shade-raid_config.txt"
        self.assertEqual(target.read_text(), "hello")


class TestGenerators(unittest.TestCase):
    def test_hyprland_generator_rendering(self):
        # Arrange
        colors = ColorTokens(colors={"background": "#F4EFE4", "inactive": "#C8C2B4"})
        metrics = MetricTokens(metrics={"border_size": "2", "gaps_inner": "10"})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        gen = HyprlandGenerator()

        # Act
        artifacts = gen.render(tokens, "shade-raid")

        # Assert
        self.assertEqual(len(artifacts), 4)
        
        # Verify colors lua
        colors_art = next(a for a in artifacts if a.artifact_id == "hyprland-colors")
        self.assertIn("background    = 0xF4EFE4", colors_art.content)
        self.assertIn("inactive      = 0xC8C2B4", colors_art.content)

        # Verify colors conf
        colors_conf_art = next(a for a in artifacts if a.artifact_id == "hyprland-colors-conf")
        self.assertIn("$background  = rgb(F4EFE4)", colors_conf_art.content)

        # Verify style lua
        style_art = next(a for a in artifacts if a.artifact_id == "hyprland-style")
        self.assertIn("border_size         = 2", style_art.content)
        self.assertIn("gaps_inner          = 10", style_art.content)

    def test_waybar_generator_rendering(self):
        # Arrange
        colors = ColorTokens(colors={"primary_surface": "#F4EFE4", "accent": "#D94F2B"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        gen = WaybarGenerator()

        # Act
        artifacts = gen.render(tokens, "shade-raid")

        # Assert
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(artifacts[0].artifact_id, "waybar-colors")
        self.assertIn("$primary_surface: #F4EFE4;", artifacts[0].content)
        self.assertIn("$accent: #D94F2B;", artifacts[0].content)
        self.assertEqual(artifacts[1].artifact_id, "waybar-variables")
        self.assertIn("$font-mono: 'monospace';", artifacts[1].content)

    def test_ghostty_generator_rendering(self):
        # Arrange
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={"font_mono": "Monaspace Radon", "font_size_md": "13"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.ghostty import GhosttyGenerator
        gen = GhosttyGenerator()
        
        # Act
        artifacts = gen.render(tokens, "shade-raid")
        
        # Assert
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "ghostty-colors")
        self.assertIn("background = F4EFE4", artifacts[0].content)
        self.assertIn("foreground = 0D0D0D", artifacts[0].content)
        self.assertIn("font-family = Monaspace Radon", artifacts[0].content)
        self.assertIn("font-size = 13", artifacts[0].content)

    def test_swaync_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D", "border": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={"font_mono": "SpaceMono"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
        gen = SwayncGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 2)
        
        config_artifact = next(a for a in artifacts if a.artifact_id == "swaync-config")
        style_artifact = next(a for a in artifacts if a.artifact_id == "swaync-style")
        
        self.assertIn("Check for Updates", config_artifact.content)
        self.assertIn("font-family: \"SpaceMono\"", style_artifact.content)
        self.assertIn("background: #F4EFE4;", style_artifact.content)
        
        # Verify preview widgets in config
        self.assertIn("label#theme-preview-title", config_artifact.content)
        self.assertIn("buttons-grid#theme-preview-image", config_artifact.content)
        self.assertIn("buttons-grid#theme-preview-palette", config_artifact.content)
        self.assertIn("buttons-grid#theme-preview-controls", config_artifact.content)
        
        # Verify MPRIS blacklist
        self.assertIn("blacklist", config_artifact.content)
        
        # Verify scrollbar hiding and animation styles
        self.assertIn(".control-center scrollbar", style_artifact.content)
        self.assertIn("scrollbar {", style_artifact.content)
        self.assertIn("#theme-preview-image button", style_artifact.content)
        self.assertIn("#theme-preview-palette button", style_artifact.content)
        self.assertIn("transition: all 160ms ease;", style_artifact.content)
        self.assertIn(".notification.removed", style_artifact.content)

    def test_swaync_preview_select_applies_preview_theme_not_active_theme(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D", "border": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={"font_mono": "SpaceMono"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            env = EnvironmentContext(home_dir=home, dotfiles_dir=home / "dotfiles", user="user")
            themes_dir = home / ".config" / "themes"
            (themes_dir / "shade-raid").mkdir(parents=True)
            (themes_dir / "ember").mkdir(parents=True)
            (themes_dir / "shade-raid" / "colors.toml").write_text('background = "#F4EFE4"\n')
            (themes_dir / "ember" / "colors.toml").write_text('background = "#111111"\naccent = "#AA3300"\n')
            (themes_dir / "current").write_text("shade-raid")
            preview_path = Path("/tmp/dotfiles_preview_theme")
            old_preview = preview_path.read_text() if preview_path.exists() else None
            preview_path.write_text("ember")
            tx = ConfigTransaction(env=env, store=ArtifactStore({}), writer=MockFileWriter())
            try:
                from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
                gen = SwayncGenerator(transaction=tx)
                artifacts = gen.render(tokens, "shade-raid")
            finally:
                if old_preview is None:
                    if preview_path.exists():
                        preview_path.unlink()
                else:
                    preview_path.write_text(old_preview)

        config_artifact = next(a for a in artifacts if a.artifact_id == "swaync-config")
        config = json.loads(config_artifact.content)
        actions = config["widget-config"]["buttons-grid#theme-preview-controls"]["actions"]
        self.assertEqual(actions[3]["label"], "Select")
        self.assertIn("configure --theme ember", actions[3]["command"])
        self.assertIn(f"{home}/.local/bin/dotfiles", actions[3]["command"])

    def test_swaync_preview_wallpaper_uses_base_theme_for_dark_variant(self):
        colors = ColorTokens(colors={"background": "#16130F", "background2": "#201C17", "foreground": "#F4EFE4", "border": "#F4EFE4"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={"font_mono": "SpaceMono"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            env = EnvironmentContext(home_dir=home, dotfiles_dir=home / "dotfiles", user="user")
            themes_dir = home / ".config" / "themes" / "shade-raid-dark"
            themes_dir.mkdir(parents=True)
            (themes_dir / "colors.toml").write_text('background = "#16130F"\n')
            wp_dir = home / "wallpapers" / "shade-raid"
            wp_dir.mkdir(parents=True)
            (wp_dir / "wall.jpg").write_text("dummy")
            tx = ConfigTransaction(env=env, store=ArtifactStore({}), writer=MockFileWriter())

            from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
            gen = SwayncGenerator(transaction=tx)
            artifacts = gen.render(tokens, "shade-raid-dark")

        style_artifact = next(a for a in artifacts if a.artifact_id == "swaync-style")
        self.assertIn(f'url("{wp_dir / "wall.jpg"}")', style_artifact.content)
        self.assertNotIn("/wallpapers/shade/", style_artifact.content)


    def test_swayosd_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D", "accent": "#D94F2B"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.swayosd import SwayosdGenerator
        gen = SwayosdGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "swayosd-colors")
        self.assertIn("$background: #F4EFE4;", artifacts[0].content)
        self.assertIn("$accent:     #D94F2B;", artifacts[0].content)

    def test_btop_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.btop import BtopGenerator
        gen = BtopGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 2)
        theme_art = next(a for a in artifacts if a.artifact_id == "btop-theme")
        self.assertIn("theme[main_bg]=\"#F4EFE4\"", theme_art.content)
        self.assertIn("theme[main_fg]=\"#0D0D0D\"", theme_art.content)

    def test_walker_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={"font_mono": "SpaceMono", "font_size_sm": "11", "font_size_md": "13"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.walker import WalkerGenerator
        gen = WalkerGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 2)
        colors_art = next(a for a in artifacts if a.artifact_id == "walker-colors")
        self.assertIn("$background:   #F4EFE4;", colors_art.content)
        config_art = next(a for a in artifacts if a.artifact_id == "walker-config")
        self.assertIn("theme = \"shade-raid\"", config_art.content)

    def test_wlogout_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.wlogout import WlogoutGenerator
        gen = WlogoutGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "wlogout-colors")
        self.assertIn("$background: #F4EFE4;", artifacts[0].content)

    def test_vesktop_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.vesktop import VesktopGenerator
        gen = VesktopGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "vesktop-theme")
        self.assertIn("--background-primary: #F4EFE4;", artifacts[0].content)

    def test_hyprlock_generator_rendering(self):
        colors = ColorTokens(colors={"lock_bg": "#000000", "lock_fg": "#FFFFFF", "accent": "#FF0000"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.hyprlock import HyprlockGenerator
        gen = HyprlockGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "hyprlock-config")
        self.assertIn("color = rgb(000000)", artifacts[0].content)

    def test_regreet_generator_rendering(self):
        colors = ColorTokens(colors={"accent": "#FF0000", "accent_fg": "#FFFFFF"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.regreet import ReGreetGenerator
        gen = ReGreetGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "regreet-style")
        self.assertIn("border: 5px solid #FF0000;", artifacts[0].content)
        self.assertIn("button {", artifacts[0].content)
        self.assertIn("background-image: none;", artifacts[0].content)
        self.assertIn("entry {", artifacts[0].content)
        self.assertIn(".destructive-action", artifacts[0].content)
        self.assertNotIn("background-color: #D94F2B;", artifacts[0].content)

    def test_greetd_generator_rendering(self):
        colors = ColorTokens(colors={})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.greetd import GreetdGenerator
        gen = GreetdGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "greetd-config")
        self.assertIn("application_prefer_dark_theme = false", artifacts[0].content)

    def test_gtk_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D"})
        metrics = MetricTokens(metrics={"cursor_theme": "Bibata", "cursor_size": "24"})
        typography = TypographyTokens(typography={"font_mono": "SpaceMono", "font_size_md": "13"})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.gtk import GtkGenerator
        gen = GtkGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 4)
        g3 = next(a for a in artifacts if a.artifact_id == "gtk3-settings")
        self.assertIn("gtk-theme-name = Adwaita", g3.content)
        self.assertIn("gtk-cursor-theme-name = Bibata", g3.content)
        g3css = next(a for a in artifacts if a.artifact_id == "gtk3-css")
        self.assertIn("background-color: #F4EFE4;", g3css.content)

    def test_plymouth_generator_rendering(self):
        colors = ColorTokens(colors={"background": "#F4EFE4", "foreground": "#0D0D0D", "accent": "#D94F2B"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        from dotfiles_api.infrastructure.generators.plymouth import PlymouthGenerator
        gen = PlymouthGenerator()
        artifacts = gen.render(tokens, "shade-raid")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "plymouth-theme")
        self.assertIn("SHADE RAID", artifacts[0].content)
