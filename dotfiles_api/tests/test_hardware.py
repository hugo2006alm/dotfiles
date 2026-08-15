import tempfile
import unittest
from pathlib import Path

from dotfiles_api.application.hardware import (
    detect_gpu_vendors,
    graphics_packages_for,
    kernel_headers_package,
)
from dotfiles_api.application.profiles.desktop import build_desktop_profile


class TestGraphicsDetection(unittest.TestCase):
    def test_detects_gpu_vendors_from_drm_sysfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            drm_root = Path(tmp)
            for card, vendor in [("card0", "0x1002"), ("card1", "0x8086")]:
                vendor_file = drm_root / card / "device" / "vendor"
                vendor_file.parent.mkdir(parents=True)
                vendor_file.write_text(vendor)

            self.assertEqual(detect_gpu_vendors(drm_root), ["amd", "intel"])

    def test_amd_stack_is_selected_without_intel_or_nvidia_drivers(self) -> None:
        packages = graphics_packages_for(["amd"])

        self.assertIn("mesa", packages)
        self.assertIn("lib32-mesa", packages)
        self.assertIn("vulkan-radeon", packages)
        self.assertIn("lib32-vulkan-radeon", packages)
        self.assertIn("libva-mesa-driver", packages)
        self.assertNotIn("vulkan-intel", packages)
        self.assertNotIn("nvidia-open-dkms", packages)

    def test_intel_stack_is_selected(self) -> None:
        packages = graphics_packages_for(["intel"])

        self.assertIn("vulkan-intel", packages)
        self.assertIn("lib32-vulkan-intel", packages)
        self.assertIn("intel-media-driver", packages)
        self.assertNotIn("vulkan-radeon", packages)

    def test_nvidia_stack_uses_dkms_and_matching_kernel_headers(self) -> None:
        packages = graphics_packages_for(["nvidia"], kernel_release="6.18.1-arch1-1")

        self.assertIn("nvidia-open-dkms", packages)
        self.assertIn("nvidia-utils", packages)
        self.assertIn("lib32-nvidia-utils", packages)
        self.assertIn("linux-headers", packages)

    def test_kernel_header_mapping(self) -> None:
        self.assertEqual(kernel_headers_package("6.18.1-arch1-1"), "linux-headers")
        self.assertEqual(kernel_headers_package("6.18.1-lts"), "linux-lts-headers")
        self.assertEqual(kernel_headers_package("6.18.1-zen1-1-zen"), "linux-zen-headers")
        self.assertEqual(kernel_headers_package("6.18.1-hardened1-1-hardened"), "linux-hardened-headers")

    def test_desktop_profile_uses_detected_graphics_packages(self) -> None:
        profile = build_desktop_profile(graphics_packages=["mesa", "vulkan-intel"])
        packages = profile.get_packages()

        self.assertIn("mesa", packages)
        self.assertIn("vulkan-intel", packages)
        self.assertNotIn("vulkan-radeon", packages)
        self.assertNotIn("lib32-vulkan-radeon", packages)


if __name__ == "__main__":
    unittest.main()
