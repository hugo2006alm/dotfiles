import unittest
import tempfile
import shutil
from pathlib import Path
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.file_writer import SystemFileWriter

class MockExecutor:
    def __init__(self):
        self.commands = []
        self.results = {}

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        cmd_str = " ".join(args)
        self.commands.append(cmd_str)
        return self.results.get(cmd_str, CommandResult(stdout="mocked", stderr="", returncode=0))

class TestEnvironmentContext(unittest.TestCase):
    def test_environment_context_properties(self):
        # Act
        ctx = EnvironmentContext(
            home_dir=Path("/home/user"),
            dotfiles_dir=Path("/home/user/dotfiles"),
            user="user"
        )
        # Assert
        self.assertEqual(ctx.home_dir, Path("/home/user"))
        self.assertEqual(ctx.dotfiles_dir, Path("/home/user/dotfiles"))
        self.assertEqual(ctx.user, "user")

class TestExecutionContext(unittest.TestCase):
    def test_execution_normal_mode(self):
        # Arrange
        mock_exec = MockExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=mock_exec)

        # Act
        res = exec_ctx.execute(["echo", "hello"])

        # Assert
        self.assertEqual(res.stdout, "mocked")
        self.assertEqual(len(mock_exec.commands), 1)
        self.assertEqual(mock_exec.commands[0], "echo hello")

    def test_execution_dry_run_mode(self):
        # Arrange
        mock_exec = MockExecutor()
        exec_ctx = ExecutionContext(dry_run=True, executor=mock_exec)

        # Act
        res = exec_ctx.execute(["echo", "hello"])

        # Assert
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout, "")
        self.assertEqual(len(mock_exec.commands), 0)

class TestSystemFileWriter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_file_writing(self):
        # Arrange
        writer = SystemFileWriter()
        target = Path(self.temp_dir) / "test.txt"

        # Act
        writer.write(target, "hello world")

        # Assert
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "hello world")

class TestFileThemeStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env = EnvironmentContext(
            home_dir=self.temp_dir,
            dotfiles_dir=self.temp_dir / "dotfiles",
            user="user"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_and_set_active_theme(self):
        # Arrange
        store = FileThemeStore(env=self.env)
        theme_file = self.temp_dir / ".config" / "themes" / "current"

        # Assert default
        self.assertEqual(store.get_active_theme(), "shade-raid")

        # Act
        store.set_active_theme("catppuccin")

        # Assert updated
        self.assertEqual(store.get_active_theme(), "catppuccin")
        self.assertTrue(theme_file.exists())
        self.assertEqual(theme_file.read_text().strip(), "catppuccin")
