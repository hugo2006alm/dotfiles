import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

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
        if "user.name" in args:
            return CommandResult(stdout="Mock User", stderr="", returncode=0)
        if "user.email" in args:
            return CommandResult(stdout="mock@example.com", stderr="", returncode=0)
        return CommandResult(stdout="", stderr="", returncode=0)

class TestSetupServices(unittest.TestCase):
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

    def test_services_setup_service(self) -> None:
        from dotfiles_api.application.services.services import ServicesSetupService
        svc = ServicesSetupService(self.exec_ctx, self.env)
        svc.setup_services()

        # Check that systemctl commands were called
        self.assertTrue(any("systemctl enable NetworkManager" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("ufw enable" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("sudoers.d" in cmd for cmd in self.executor.commands))

    def test_user_setup_service(self) -> None:
        from dotfiles_api.application.services.user import UserSetupService
        svc = UserSetupService(self.exec_ctx, self.env)
        
        # Test runs git configs, Default shell etc.
        svc.setup_user(setup_github=False)
        self.assertTrue(any("chsh -s /usr/bin/fish" in cmd for cmd in self.executor.commands))
        self.assertTrue(any("fc-cache" in cmd for cmd in self.executor.commands))
        self.assertTrue((self.env.home_dir / ".config" / "gtk-3.0" / "bookmarks").exists())

    def test_extras_setup_service(self) -> None:
        from dotfiles_api.application.services.extras import ExtrasSetupService
        # Setup mock directories for spotify
        spotify_path = Path(self.temp_dir) / "opt" / "spotify"
        spotify_path.mkdir(parents=True)
        prefs_file = self.env.home_dir / ".config" / "spotify" / "prefs"
        prefs_file.parent.mkdir(parents=True)
        prefs_file.write_text("prefs")

        svc = ExtrasSetupService(self.exec_ctx, self.env)
        # Mock paths
        svc._spotify_path = spotify_path
        svc._prefs_path = prefs_file

        svc.setup_extras()
        self.assertTrue(any("spicetify backup apply" in cmd for cmd in self.executor.commands))

    def test_setup_service(self) -> None:
        from dotfiles_api.application.services.setup import SetupService
        mock_install_service = MagicMock()
        mock_linker = MagicMock()
        mock_theme_service = MagicMock()
        mock_services = MagicMock()
        mock_user = MagicMock()
        mock_extras = MagicMock()

        svc = SetupService(
            env=self.env,
            exec_ctx=self.exec_ctx,
            install_service=mock_install_service,
            linker=mock_linker,
            theme_service=mock_theme_service,
            services_service=mock_services,
            user_service=mock_user,
            extras_service=mock_extras
        )
        svc.run_setup(setup_github=True)

        mock_install_service.install_profile.assert_called_once()
        mock_linker.link.assert_called_once()
        mock_services.setup_services.assert_called_once()
        mock_user.setup_user.assert_called_once_with(setup_github=True)
        mock_theme_service.apply_theme.assert_called_once_with("shade-raid")
        mock_extras.setup_extras.assert_called_once()
