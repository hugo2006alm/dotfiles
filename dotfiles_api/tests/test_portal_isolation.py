import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.application.services.wayland_session import WaylandSessionService
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
from dotfiles_api.infrastructure.executor import SystemCommandExecutor


class TestPortalIsolation(unittest.TestCase):
    def test_real_fake_tools_isolate_unit_and_portal_failures(self):
        registry = ApplicationRegistry(APPLICATIONS)
        units = [spec.user_unit for spec in registry.specs if spec.user_unit]
        portal = "xdg-desktop-portal.service"
        scenarios = (
            {"shade-raid-walker.service"},
            {"shade-raid-elephant.service", "shade-raid-waybar.service", "shade-raid-swayosd.service"},
            {"shade-raid-walker.service", portal},
            {"daemon-reload"},
        )
        for failures in scenarios:
            with self.subTest(failures=failures), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                calls = root / "calls.jsonl"
                script = (
                    f"#!{sys.executable}\n"
                    "import json,os,sys\n"
                    "from pathlib import Path\n"
                    "tool=Path(sys.argv[0]).name\n"
                    "with open(os.environ['SHADE_TEST_CALLS'],'a') as stream:\n"
                    " stream.write(json.dumps([tool,*sys.argv[1:]])+'\\n')\n"
                    "failures=set(json.loads(os.environ['SHADE_TEST_FAILURES']))\n"
                    "if tool=='systemctl' and failures.intersection(sys.argv[1:]):\n"
                    " print('injected failure for '+sys.argv[-1],file=sys.stderr)\n"
                    " sys.exit(7)\n"
                )
                for name in ("systemctl", "dbus-update-activation-environment"):
                    path = root / name
                    path.write_text(script)
                    path.chmod(0o700)
                environment = {
                    "PATH": str(root), "WAYLAND_DISPLAY": "wayland-test",
                    "XDG_CURRENT_DESKTOP": "Hyprland", "XDG_SESSION_TYPE": "wayland",
                    "SHADE_TEST_CALLS": str(calls), "SHADE_TEST_FAILURES": json.dumps(sorted(failures)),
                }
                service = WaylandSessionService(ExecutionContext(False, SystemCommandExecutor()), registry)
                with patch.dict(os.environ, environment, clear=True):
                    with self.assertRaises(RuntimeError) as error:
                        service.start()
                commands = [json.loads(line) for line in calls.read_text().splitlines()]
                self.assertEqual(commands[0][0], "dbus-update-activation-environment")
                self.assertEqual(commands[1], ["systemctl", "--user", "daemon-reload"])
                self.assertEqual(commands[-1], ["systemctl", "--user", "start", portal])
                self.assertEqual(commands.count(["systemctl", "--user", "start", portal]), 1)
                if "daemon-reload" in failures:
                    self.assertEqual(len(commands), 3)
                else:
                    for unit in units:
                        self.assertEqual(commands.count(["systemctl", "--user", "start", unit]), 1)
                    for failed in failures:
                        self.assertIn(failed, str(error.exception))
                self.assertFalse(any("restart" in command or "stop" in command for command in commands))

    def test_walker_keeps_real_systemd_dependency_on_elephant(self):
        root = Path(__file__).resolve().parents[2]
        unit = (root / "home/.config/systemd/user/shade-raid-walker.service").read_text()
        self.assertIn("Requires=shade-raid-elephant.service", unit)
        self.assertIn("After=shade-raid-elephant.service", unit)

    def test_managed_fish_aliases_use_systemd_only(self):
        root = Path(__file__).resolve().parents[2]
        aliases = (root / "home/.config/fish/config.fish").read_text().splitlines()
        for name in ("waybar", "walker"):
            line = next(line for line in aliases if line.startswith(f"alias reload-{name}="))
            self.assertIn("systemctl --user", line)
            self.assertIn(f"shade-raid-{name}.service", line)
            self.assertNotIn("pkill", line)
            self.assertNotIn("hyprctl", line)
        line = next(line for line in aliases if line.startswith("alias reload-swaync="))
        self.assertIn("swaync-client -R", line)
        self.assertIn("swaync-client -rs", line)
        self.assertNotIn("pkill", line)
