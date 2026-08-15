import platform
from pathlib import Path


GPU_VENDOR_IDS = {
    "0x1002": "amd",
    "0x8086": "intel",
    "0x10de": "nvidia",
}

COMMON_GRAPHICS_PACKAGES = [
    "mesa",
    "lib32-mesa",
    "libva-utils",
    "gamescope",
]

GPU_GRAPHICS_PACKAGES = {
    "amd": [
        "vulkan-radeon",
        "lib32-vulkan-radeon",
        "libva-mesa-driver",
    ],
    "intel": [
        "vulkan-intel",
        "lib32-vulkan-intel",
        "intel-media-driver",
    ],
    "nvidia": [
        "nvidia-open-dkms",
        "nvidia-utils",
        "lib32-nvidia-utils",
    ],
}


def detect_gpu_vendors(drm_root: Path = Path("/sys/class/drm")) -> list[str]:
    vendors: list[str] = []

    for vendor_file in sorted(drm_root.glob("card*/device/vendor")):
        try:
            vendor_id = vendor_file.read_text().strip().lower()
        except OSError:
            continue

        vendor = GPU_VENDOR_IDS.get(vendor_id)
        if vendor and vendor not in vendors:
            vendors.append(vendor)

    return vendors


def kernel_headers_package(kernel_release: str | None = None) -> str | None:
    release = (kernel_release or platform.release()).lower()

    if "-lts" in release:
        return "linux-lts-headers"
    if "-zen" in release:
        return "linux-zen-headers"
    if "-hardened" in release:
        return "linux-hardened-headers"
    if "arch" in release:
        return "linux-headers"

    return None


def graphics_packages_for(
    vendors: list[str],
    kernel_release: str | None = None,
) -> list[str]:
    packages = list(COMMON_GRAPHICS_PACKAGES)

    for vendor in ("amd", "intel", "nvidia"):
        if vendor not in vendors:
            continue
        packages.extend(GPU_GRAPHICS_PACKAGES[vendor])

        if vendor == "nvidia":
            headers = kernel_headers_package(kernel_release)
            if headers:
                packages.append(headers)

    return list(dict.fromkeys(packages))


def detect_graphics_packages() -> list[str]:
    return graphics_packages_for(detect_gpu_vendors())
