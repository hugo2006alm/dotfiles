import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult


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
        action = CommandAction(self.exec_ctx, [["echo", "hello"]])
        action.execute(["world"])
        self.assertEqual(self.executor.commands[0], "echo hello world")

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

        action.execute([])
        self.assertTrue(any("grim" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("notify-send" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("wl-copy" in cmd and cmd.endswith("&") for cmd in self.executor.commands))

        action.execute(["--region"])
        self.assertTrue(any("slurp" in cmd for cmd in self.executor.commands))

    @patch("subprocess.Popen")
    def test_recorder_action_toggle(self, mock_popen) -> None:
        from dotfiles_api.infrastructure.actions.recorder import RecorderAction
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        action = RecorderAction(self.exec_ctx)

        action.execute([])
        mock_popen.assert_called_once()
        self.assertTrue(action._pid_file.exists())
        self.assertEqual(action._pid_file.read_text(), "12345")

        self.executor.mock_results = {
            "kill -0 12345": ("", "", 0),
            "pgrep -f wf-recorder": ("12345\n", "", 0),
        }
        action.execute([])
        self.assertTrue(any("kill -INT 12345" in cmd for cmd in self.executor.commands))

    def test_portal_action(self) -> None:
        from dotfiles_api.infrastructure.actions.portal import PortalAction
        action = PortalAction(self.exec_ctx)
        action.execute([])
        self.assertTrue(any("killall" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("xdg-desktop-portal-hyprland" in cmd for cmd in self.executor.commands))

    def test_drawer_action(self) -> None:
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

        wp_dir = self.env.home_dir / "wallpapers" / "shade-raid"
        wp_dir.mkdir(parents=True)
        (wp_dir / "wall.jpg").write_text("dummy")

        action.execute([])

        self.assertTrue(any("awww img" in cmd for cmd in self.executor.commands))
        cache_wp = self.env.home_dir / ".cache" / "shade-raid" / "last_wallpaper"
        self.assertTrue(cache_wp.exists())
        self.assertIn("wall.jpg", cache_wp.read_text())

    def test_wallpaper_action_falls_back_to_base_theme_for_dark_variant(self) -> None:
        from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction
        action = WallpaperAction(self.exec_ctx, self.env)

        themes_dir = self.env.home_dir / ".config" / "themes"
        themes_dir.mkdir(parents=True)
        (themes_dir / "current").write_text("shade-raid-dark")

        wp_dir = self.env.home_dir / "wallpapers" / "shade-raid"
        wp_dir.mkdir(parents=True)
        (wp_dir / "wall.jpg").write_text("dummy")

        action.execute([])

        self.assertTrue(any("wallpapers/shade-raid/wall.jpg" in cmd for cmd in self.executor.commands))
        self.assertFalse(any("wallpapers/shade/wall.jpg" in cmd for cmd in self.executor.commands))

    def test_preview_action(self) -> None:
        from dotfiles_api.infrastructure.actions.preview import PreviewAction
        action = PreviewAction(self.exec_ctx, self.env)

        themes_dir = self.env.home_dir / ".config" / "themes"
        theme_a = themes_dir / "theme-a"
        theme_b = themes_dir / "theme-b"
        theme_a.mkdir(parents=True)
        theme_b.mkdir(parents=True)
        (theme_a / "colors.toml").write_text("")
        (theme_b / "colors.toml").write_text("")
        (themes_dir / "current").write_text("theme-a")

        preview_temp = Path("/tmp/dotfiles_preview_theme")
        if preview_temp.exists():
            preview_temp.unlink()

        action.execute(["next"])

        self.assertTrue(preview_temp.exists())
        self.assertEqual(preview_temp.read_text().strip(), "theme-b")
        self.assertTrue(any("swaync-client -R" in cmd for cmd in self.executor.commands))

        action.execute(["prev"])
        self.assertEqual(preview_temp.read_text().strip(), "theme-a")


if __name__ == "__main__":
    unittest.main()
