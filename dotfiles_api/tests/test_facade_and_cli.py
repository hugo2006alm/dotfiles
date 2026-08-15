import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.application.facade import DotfilesFacade


class MockLinker:
    def __init__(self):
        self.linked = False

    def link(self, src: Path, dest: Path) -> None:
        self.linked = True


class MockInstallService:
    def __init__(self):
        self.profile = None

    def install_profile(self, profile: Profile) -> None:
        self.profile = profile


class MockThemeService:
    def __init__(self):
        self.theme = None

    def apply_theme(self, theme_name: str) -> None:
        self.theme = theme_name


class MockReloadService:
    def __init__(self):
        self.reloaded = False

    def reload_all(self) -> None:
        self.reloaded = True


class TestDotfilesFacade(unittest.TestCase):
    def test_facade_operations(self):
        env = EnvironmentContext(home_dir=Path("/home/user"), dotfiles_dir=Path("/home/user/dotfiles"), user="user")
        exec_ctx = ExecutionContext(dry_run=True, executor=None)

        linker = MockLinker()
        install_svc = MockInstallService()
        theme_svc = MockThemeService()
        reload_svc = MockReloadService()

        facade = DotfilesFacade(
            env=env,
            exec_ctx=exec_ctx,
            install_service=install_svc,
            theme_service=theme_svc,
            reload_service=reload_svc,
            linker=linker,
        )

        facade.link()
        self.assertTrue(linker.linked)

        facade.apply_theme("shade-raid")
        self.assertEqual(theme_svc.theme, "shade-raid")

        p = Profile(name="test", features=[])
        facade.apply_profile(p)
        self.assertEqual(install_svc.profile, p)

        facade.reload()
        self.assertTrue(reload_svc.reloaded)


class TestCliToggle(unittest.TestCase):
    def _theme_home(self) -> tempfile.TemporaryDirectory:
        temp_dir = tempfile.TemporaryDirectory()
        themes_dir = Path(temp_dir.name) / ".config" / "themes"
        (themes_dir / "shade-raid").mkdir(parents=True)
        (themes_dir / "shade-raid-dark").mkdir(parents=True)
        return temp_dir

    @patch("argparse.ArgumentParser.parse_args")
    @patch("dotfiles_api.presentation.cli.DotfilesFacade")
    @patch("dotfiles_api.presentation.cli.FileThemeStore")
    def test_cli_toggle_to_dark(self, mock_theme_store_class, mock_facade_class, mock_parse_args):
        mock_theme_store = mock_theme_store_class.return_value
        mock_theme_store.get_active_theme.return_value = "shade-raid"
        mock_facade = mock_facade_class.return_value
        mock_parse_args.return_value = argparse.Namespace(command="toggle", dry_run=False, theme="shade-raid", verbose=False)

        from dotfiles_api.presentation.cli import main

        with self._theme_home() as temp_home, patch("dotfiles_api.presentation.cli.Path.home", return_value=Path(temp_home)):
            main()

        mock_facade.apply_theme.assert_called_once_with("shade-raid-dark")
        mock_facade.reload.assert_not_called()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("dotfiles_api.presentation.cli.DotfilesFacade")
    @patch("dotfiles_api.presentation.cli.FileThemeStore")
    def test_cli_toggle_to_light(self, mock_theme_store_class, mock_facade_class, mock_parse_args):
        mock_theme_store = mock_theme_store_class.return_value
        mock_theme_store.get_active_theme.return_value = "shade-raid-dark"
        mock_facade = mock_facade_class.return_value
        mock_parse_args.return_value = argparse.Namespace(command="toggle", dry_run=False, theme="shade-raid", verbose=False)

        from dotfiles_api.presentation.cli import main

        with self._theme_home() as temp_home, patch("dotfiles_api.presentation.cli.Path.home", return_value=Path(temp_home)):
            main()

        mock_facade.apply_theme.assert_called_once_with("shade-raid")
        mock_facade.reload.assert_not_called()


class TestCliCommands(unittest.TestCase):
    @patch("argparse.ArgumentParser.parse_args")
    @patch("dotfiles_api.presentation.cli.DotfilesFacade")
    def test_cli_setup(self, mock_facade_class, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(command="setup", dry_run=False, theme="shade-raid", github=True)
        mock_facade = mock_facade_class.return_value

        from dotfiles_api.presentation.cli import main
        main()

        mock_facade.setup.assert_called_once_with(setup_github=True)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("dotfiles_api.presentation.cli.ActionService")
    def test_cli_action(self, mock_action_svc_class, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(command="action", dry_run=False, theme="shade-raid", action_name="screenshot", action_args=["--region"])
        mock_action_svc = mock_action_svc_class.return_value

        from dotfiles_api.presentation.cli import main
        main()

        mock_action_svc.run_action.assert_called_once_with("screenshot", ["--region"])

    @patch("argparse.ArgumentParser.parse_args")
    @patch("dotfiles_api.presentation.cli.ActionService")
    @patch("dotfiles_api.presentation.cli.DotfilesFacade")
    def test_cli_configure_changes_wallpaper_after_theme(self, mock_facade_class, mock_action_svc_class, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(command="configure", dry_run=False, theme="shade-raid-dark", verbose=False)
        mock_action_svc = mock_action_svc_class.return_value
        mock_facade = mock_facade_class.return_value

        from dotfiles_api.presentation.cli import main
        main()

        mock_facade.apply_theme.assert_called_once_with("shade-raid-dark")
        mock_action_svc.run_action.assert_called_with("wallpaper", [])


if __name__ == "__main__":
    unittest.main()
