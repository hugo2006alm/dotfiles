import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.domain.tokens import ColorTokens, MetricTokens, TypographyTokens, DesignTokens
from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator


class TestSwayncCommandQuoting(unittest.TestCase):
    def test_theme_controls_execute_with_spaces_and_quotes_without_shell_expansion(self):
        with tempfile.TemporaryDirectory(prefix="swaync quoted ") as temporary:
            home = Path(temporary) / "user's home"
            executable = home / ".local/bin/dotfiles"
            executable.parent.mkdir(parents=True)
            executable.write_text(f"#!{sys.executable}\n" +
                "import json, os, sys\nfrom pathlib import Path\n" +
                "Path(os.environ['SWAYNC_TEST_ARGS']).write_text(json.dumps(sys.argv[1:]))\n")
            executable.chmod(0o700)
            selected = "personal ' $(touch SHOULD_NOT_EXIST)"
            for theme in ("active", selected):
                directory = home / ".config/themes" / theme
                directory.mkdir(parents=True)
                (directory / "colors.toml").write_text("[colors]\n")
            env = EnvironmentContext(home, Path(temporary) / "repo", "tester")
            tokens = DesignTokens(ColorTokens({}), MetricTokens({}), TypographyTokens({}))
            preview_file = env.runtime_dir / "preview-theme"
            preview_file.parent.mkdir(parents=True, exist_ok=True)
            preview_file.write_text(selected)
            artifacts = SwayncGenerator(transaction=Mock(env=env)).render(tokens, "active")
            config = json.loads(next(item.content for item in artifacts if item.artifact_id == "swaync-config"))
            controls = config["widget-config"]["buttons-grid#theme-preview-controls"]["actions"]
            expected = {0: ["action", "preview", "prev"], 2: ["action", "preview", "next"],
                        3: ["configure", "--theme", selected]}
            recorded = Path(temporary) / "arguments.json"
            for index, arguments in expected.items():
                result = subprocess.run(["/bin/sh", "-c", controls[index]["command"]],
                    cwd=temporary, env={**os.environ, "SWAYNC_TEST_ARGS": str(recorded)},
                    capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(recorded.read_text()), arguments)
            self.assertFalse((Path(temporary) / "SHOULD_NOT_EXIST").exists())
