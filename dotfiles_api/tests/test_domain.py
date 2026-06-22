import unittest
from pathlib import Path
from dotfiles_api.domain.tokens import ColorTokens, MetricTokens, TypographyTokens, DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent, ConfigGeneratedEvent
from dotfiles_api.domain.models import Feature, Profile

class TestDomainTokens(unittest.TestCase):
    def test_tokens_structure(self):
        # Arrange
        colors = ColorTokens(colors={"primary_surface": "#F4EFE4", "accent": "#D94F2B"})
        metrics = MetricTokens(metrics={"border_size": 2, "gaps_inner": 10})
        typography = TypographyTokens(typography={"sans_font": "Outfit", "font_size": 11})

        # Act
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)

        # Assert
        self.assertEqual(tokens.colors.colors["primary_surface"], "#F4EFE4")
        self.assertEqual(tokens.metrics.metrics["border_size"], 2)
        self.assertEqual(tokens.typography.typography["sans_font"], "Outfit")

class TestGeneratedArtifact(unittest.TestCase):
    def test_artifact_structure(self):
        # Act
        artifact = GeneratedArtifact(artifact_id="test-id", content="test-content")

        # Assert
        self.assertEqual(artifact.artifact_id, "test-id")
        self.assertEqual(artifact.content, "test-content")

class TestEventBus(unittest.TestCase):
    def test_typed_subscription_and_publishing(self):
        # Arrange
        bus = EventBus()
        theme_events = []
        config_events = []

        def theme_handler(event: ThemeChangedEvent):
            theme_events.append(event)

        def config_handler(event: ConfigGeneratedEvent):
            config_events.append(event)

        bus.subscribe(ThemeChangedEvent, theme_handler)
        bus.subscribe(ConfigGeneratedEvent, config_handler)

        colors = ColorTokens(colors={})
        metrics = MetricTokens(metrics={})
        typography = TypographyTokens(typography={})
        tokens = DesignTokens(colors=colors, metrics=metrics, typography=typography)
        
        theme_event = ThemeChangedEvent(theme_name="shade-raid", tokens=tokens)
        config_event = ConfigGeneratedEvent(generator_name="waybar")

        # Act
        bus.publish(theme_event)
        bus.publish(config_event)

        # Assert
        self.assertEqual(len(theme_events), 1)
        self.assertEqual(theme_events[0], theme_event)
        self.assertEqual(len(config_events), 1)
        self.assertEqual(config_events[0], config_event)

    def test_unsubscribed_event_not_dispatched(self):
        # Arrange
        bus = EventBus()
        events = []
        bus.subscribe(ThemeChangedEvent, lambda e: events.append(e))

        config_event = ConfigGeneratedEvent(generator_name="waybar")

        # Act
        bus.publish(config_event)

        # Assert
        self.assertEqual(len(events), 0)

class TestProfileAndFeature(unittest.TestCase):
    def test_package_aggregation_without_duplicates(self):
        # Arrange
        f1 = Feature(name="launcher", packages=["walker", "rofi"], capabilities=["launcher"])
        f2 = Feature(name="terminal", packages=["ghostty", "walker"], capabilities=["terminal"])
        
        # Act
        profile = Profile(name="desktop", features=[f1, f2])

        # Assert
        packages = profile.get_packages()
        self.assertEqual(len(packages), 3)
        self.assertIn("walker", packages)
        self.assertIn("rofi", packages)
        self.assertIn("ghostty", packages)
