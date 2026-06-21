import unittest
import tempfile
import shutil
from pathlib import Path
from dotfiles_api.domain.tokens import ColorTokens, MetricTokens, TypographyTokens, DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.infrastructure.generators.hypr import HyprlandGenerator
from dotfiles_api.infrastructure.generators.waybar import WaybarGenerator

class MockArtifactStore:
    def __init__(self, mappings):
        self.mappings = mappings

    def resolve_path(self, artifact_id: str) -> Path:
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

class TestGenerators(unittest.TestCase):
    def test_hyprland_generator_rendering(self):
        # Arrange
        colors = ColorTokens(colors={"primary_surface": "#F4EFE4", "inactive": "#C8C2B4"})
        metrics = MetricTokens(metrics={"border_size": 2, "gaps_inner": 10})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        gen = HyprlandGenerator()

        # Act
        artifacts = gen.render(tokens)

        # Assert
        self.assertEqual(len(artifacts), 2)
        
        # Verify colors artifact
        colors_art = next(a for a in artifacts if a.artifact_id == "hyprland-colors")
        self.assertIn("primary_surface = '#F4EFE4'", colors_art.content)
        self.assertIn("inactive = '#C8C2B4'", colors_art.content)

        # Verify style artifact
        style_art = next(a for a in artifacts if a.artifact_id == "hyprland-style")
        self.assertIn("border_size = 2", style_art.content)
        self.assertIn("gaps_inner = 10", style_art.content)

    def test_waybar_generator_rendering(self):
        # Arrange
        colors = ColorTokens(colors={"primary_surface": "#F4EFE4", "accent": "#D94F2B"})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        gen = WaybarGenerator()

        # Act
        artifacts = gen.render(tokens)

        # Assert
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].artifact_id, "waybar-colors")
        self.assertIn("$primary_surface: #F4EFE4;", artifacts[0].content)
        self.assertIn("$accent: #D94F2B;", artifacts[0].content)
