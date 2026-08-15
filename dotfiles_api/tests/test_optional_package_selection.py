import unittest

from dotfiles_api.application.package_catalog import OPTIONAL_PACKAGES
from dotfiles_api.application.profiles.desktop import build_desktop_profile
from dotfiles_api.application.services.optional_packages import OptionalPackageSelectionService


class TestOptionalPackageSelection(unittest.TestCase):
    def test_base_profile_contains_corrected_core_packages(self) -> None:
        profile = build_desktop_profile()
        packages = profile.get_packages()

        for package in [
            "networkmanager-openvpn",
            "rate-mirrors",
            "swayosd",
            "mise",
            "plymouth",
            "wlogout",
            "noto-fonts-emoji",
            "ttf-space-mono-nerd",
        ]:
            self.assertIn(package, packages)

        for package in [
            "network-manager-openvpn",
            "reflector",
            "swayosd-git",
            "mise-bin",
            "rofi-wayland",
        ]:
            self.assertNotIn(package, packages)

    def test_optional_packages_are_not_in_base_profile(self) -> None:
        packages = build_desktop_profile().get_packages()
        for option in OPTIONAL_PACKAGES:
            self.assertNotIn(option["package"], packages)

    def test_selected_optional_packages_are_added_to_profile(self) -> None:
        profile = build_desktop_profile(["docker", "obs-studio", "android-studio"])
        packages = profile.get_packages()
        self.assertIn("docker", packages)
        self.assertIn("obs-studio", packages)
        self.assertIn("android-studio", packages)

    def test_selector_supports_all_none_toggle_and_confirmation(self) -> None:
        options = [
            {"package": "one", "label": "One", "category": "Test", "source": "pacman"},
            {"package": "two", "label": "Two", "category": "Test", "source": "yay"},
            {"package": "three", "label": "Three", "category": "Test", "source": "pacman"},
        ]
        answers = iter(["a", "2", "c", "y"])
        output: list[str] = []
        selector = OptionalPackageSelectionService(
            input_fn=lambda _prompt: next(answers),
            output_fn=output.append,
        )

        selected = selector.select(options)

        self.assertEqual(selected, ["one", "three"])
        self.assertTrue(any("Selected packages" in line for line in output))

    def test_selector_can_start_from_none_then_enable_individual_packages(self) -> None:
        options = [
            {"package": "one", "label": "One", "category": "Test", "source": "pacman"},
            {"package": "two", "label": "Two", "category": "Test", "source": "yay"},
        ]
        answers = iter(["n", "1", "c", "y"])
        selector = OptionalPackageSelectionService(
            input_fn=lambda _prompt: next(answers),
            output_fn=lambda _line: None,
        )

        self.assertEqual(selector.select(options), ["one"])

    def test_selector_reopens_menu_when_confirmation_is_rejected(self) -> None:
        options = [
            {"package": "one", "label": "One", "category": "Test", "source": "pacman"},
            {"package": "two", "label": "Two", "category": "Test", "source": "pacman"},
        ]
        answers = iter(["1", "c", "n", "2", "c", "y"])
        selector = OptionalPackageSelectionService(
            input_fn=lambda _prompt: next(answers),
            output_fn=lambda _line: None,
        )

        self.assertEqual(selector.select(options), ["one", "two"])

    def test_antigravity_variants_are_mutually_exclusive(self) -> None:
        options = [
            {
                "package": "antigravity",
                "label": "Antigravity",
                "category": "Development",
                "source": "yay",
                "conflicts": ["antigravity-ide"],
            },
            {
                "package": "antigravity-ide",
                "label": "Antigravity IDE",
                "category": "Development",
                "source": "yay",
                "conflicts": ["antigravity"],
            },
        ]
        answers = iter(["1", "2", "c", "y"])
        selector = OptionalPackageSelectionService(
            input_fn=lambda _prompt: next(answers),
            output_fn=lambda _line: None,
        )

        self.assertEqual(selector.select(options), ["antigravity-ide"])


if __name__ == "__main__":
    unittest.main()
