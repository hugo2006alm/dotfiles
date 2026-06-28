import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult

# Mock Command Executor
class MockCommandExecutor:
    def __init__(self):
        self.commands = []
        self.mock_results = {}

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        cmd_str = " ".join(args)
        self.commands.append(cmd_str)
        for k, v in self.mock_results.items():
            if k in cmd_str:
                return CommandResult(stdout=v[0], stderr=v[1], returncode=v[2])
        return CommandResult(stdout="", stderr="", returncode=0)

class TestActions(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.env = EnvironmentContext(
            home_dir=Path(self.temp_dir),
            dotfiles_dir=Path(self.temp_dir) / "dotfiles",
            user="user"
        )
        self.executor = MockCommandExecutor()
        self.exec_ctx = ExecutionContext(dry_run=False, executor=self.executor)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_command_action(self) -> None:
        from dotfiles_api.infrastructure.actions.command import CommandAction
        # Single command
        action = CommandAction(self.exec_ctx, [["echo", "hello"]])
        action.execute(["world"])
        self.assertEqual(self.executor.commands[0], "echo hello world")

        # Multi-command
        action_multi = CommandAction(self.exec_ctx, [["pkill", "waybar"], ["hyprctl", "dispatch"]])
        action_multi.execute([])
        self.assertIn("pkill waybar", self.executor.commands[1])
        self.assertIn("hyprctl dispatch", self.executor.commands[2])

    def test_action_service_registry(self) -> None:
        from dotfiles_api.application.services.action import ActionService
        service = ActionService()
        mock_action = MagicMock()
        service.register("test", mock_action)
        service.run_action("test", ["arg"])
        mock_action.execute.assert_called_once_with(["arg"])

    def test_screenshot_action(self) -> None:
        from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
        action = ScreenshotAction(self.exec_ctx)
        
        # Test full screen
        action.execute([])
        self.assertTrue(any("grim" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("notify-send" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("wl-copy" in cmd and cmd.endswith("&") for cmd in self.executor.commands))

        # Test region
        action.execute(["--region"])
        self.assertTrue(any("slurp" in cmd for cmd in self.executor.commands))

    def test_recorder_action_toggle(self) -> None:
        from dotfiles_api.infrastructure.actions.recorder import RecorderAction
        action = RecorderAction(self.exec_ctx)

        # Starts recording
        action.execute([])
        self.assertTrue(any("wf-recorder" in cmd for cmd in self.executor.commands))

        # Stops recording (mock PID file exists)
        self.executor.mock_results = {"pgrep -f wf-recorder": ("12345\n", "", 0)}
        action.execute([])
        self.assertTrue(any("kill -INT" in cmd for cmd in self.executor.commands or "pkill -INT" in cmd))

    def test_portal_action(self) -> None:
        from dotfiles_api.infrastructure.actions.portal import PortalAction
        action = PortalAction(self.exec_ctx)
        action.execute([])
        self.assertTrue(any("killall" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("xdg-desktop-portal-hyprland" in cmd for cmd in self.executor.commands))

    def test_drawer_action(self) -> None:
        # Mock hyprctl monitors json
        self.executor.mock_results = {
            "hyprctl monitors -j": ('[{"focused": true, "width": 1920, "height": 1080, "scale": 1.0}]', "", 0)
        }
        from dotfiles_api.infrastructure.actions.drawer import DrawerAction
        action = DrawerAction(self.exec_ctx, self.env)
        action.execute([])
        conf_file = self.env.home_dir / ".config" / "hypr" / "drawers.lua"
        self.assertTrue(conf_file.exists())
        self.assertIn("special:btop", conf_file.read_text())

    def test_wallpaper_action(self) -> None:
        from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction
        action = WallpaperAction(self.exec_ctx, self.env)
        
        # Setup wallpapers folder
        wp_dir = self.env.home_dir / "wallpapers" / "shade-raid"
        wp_dir.mkdir(parents=True)
        (wp_dir / "wall.jpg").write_text("dummy")

        # Act
        action.execute([])

        # Assert
        self.assertTrue(any("awww img" in cmd for cmd in self.executor.commands))
        cache_wp = self.env.home_dir / ".cache" / "shade-raid" / "last_wallpaper"
        self.assertTrue(cache_wp.exists())
        self.assertIn("wall.jpg", cache_wp.read_text())

    def test_preview_action(self) -> None:
        from dotfiles_api.infrastructure.actions.preview import PreviewAction
        action = PreviewAction(self.exec_ctx, self.env)

        # Setup mock themes
        themes_dir = self.env.home_dir / ".config" / "themes"
        theme_a = themes_dir / "theme-a"
        theme_b = themes_dir / "theme-b"
        theme_a.mkdir(parents=True)
        theme_b.mkdir(parents=True)
        (theme_a / "colors.toml").write_text("")
        (theme_b / "colors.toml").write_text("")
        (themes_dir / "current").write_text("theme-a")

        # Clean preview theme temp file if it exists
        preview_temp = Path("/tmp/dotfiles_preview_theme")
        if preview_temp.exists():
            preview_temp.unlink()

        # Act: next theme (should go from theme-a to theme-b)
        action.execute(["next"])

        # Assert
        self.assertTrue(preview_temp.exists())
        self.assertEqual(preview_temp.read_text().strip(), "theme-b")
        self.assertTrue(any("swaync-client -R" in cmd for cmd in self.executor.commands))

        # Act: prev theme (should go from theme-b back to theme-a)
        action.execute(["prev"])
        self.assertEqual(preview_temp.read_text().strip(), "theme-a")

