import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestRepositoryInvariants(unittest.TestCase):
    def test_cli_uses_central_package_catalog_and_profile(self) -> None:
        source = (ROOT / "dotfiles_api" / "presentation" / "cli.py").read_text()

        self.assertNotIn("package_mapping = {", source)
        self.assertNotIn("Feature(name=\"compositor\"", source)
        self.assertIn("PackageRegistry()", source)
        self.assertIn("build_desktop_profile", source)

    def test_global_reload_includes_xdg_portals(self) -> None:
        source = (ROOT / "dotfiles_api" / "presentation" / "cli.py").read_text()

        self.assertIn("portal_reload,", source)

    def test_hyprland_uses_python_drawer_action(self) -> None:
        autostart = (ROOT / ".config" / "hypr" / "autostart.lua").read_text()
        hyprland = (ROOT / ".config" / "hypr" / "hyprland.lua").read_text()

        self.assertNotIn("gen-drawers.sh", autostart)
        self.assertNotIn("gen-drawers.sh", hyprland)
        self.assertIn("dotfiles action drawer", autostart)

    def test_bootstrap_does_not_create_partial_upgrade_state(self) -> None:
        install = (ROOT / ".config" / "install" / "install.sh").read_text()

        self.assertNotIn("pacman -Sy --noconfirm", install)
        self.assertIn("pacman -Syu --noconfirm", install)

    def test_btop_runtime_config_is_not_tracked_as_a_template(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is required to inspect tracked files")

        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".config/btop/btop.conf"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(
            result.returncode,
            0,
            ".config/btop/btop.conf must remain runtime-only and untracked",
        )


if __name__ == "__main__":
    unittest.main()
