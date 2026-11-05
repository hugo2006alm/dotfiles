import shutil
import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from dotfiles_api.domain.contracts.package_source import PackageSource
from dotfiles_api.context.execution import ExecutionContext

class YaySource(PackageSource):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def is_available(self) -> bool:
        return shutil.which("yay") is not None

    def contains(self, package: str) -> bool:
        # Read metadata over HTTPS; never invoke yay for a noninteractive query.
        url = "https://aur.archlinux.org/rpc/v5/info?" + urlencode({"arg[]": package})
        for attempt in range(2):
            try:
                with urlopen(url, timeout=15) as response:
                    data = json.load(response)
                if (not isinstance(data, dict) or data.get("type") == "error"
                        or not isinstance(data.get("results"), list)
                        or not all(isinstance(item, dict) and isinstance(item.get("Name"), str)
                                   for item in data["results"])):
                    raise ValueError("invalid AUR metadata response")
                return any(item["Name"] == package for item in data["results"])
            except HTTPError as error:
                raise RuntimeError(f"Cannot verify AUR package {package}: API HTTP error {error.code}") from error
            except (TimeoutError, socket.timeout) as error:
                if attempt == 0:
                    continue
                raise RuntimeError(f"Cannot verify AUR package {package}: network timeout") from error
            except URLError as error:
                if attempt == 0:
                    continue
                if isinstance(error.reason, (TimeoutError, socket.timeout)):
                    raise RuntimeError(f"Cannot verify AUR package {package}: network timeout") from error
                raise RuntimeError(f"Cannot verify AUR package {package}: network unavailable ({error.reason})") from error
            except (ValueError, UnicodeError) as error:
                raise RuntimeError(f"Cannot verify AUR package {package}: invalid API response") from error
            except OSError as error:
                if attempt == 0:
                    continue
                raise RuntimeError(f"Cannot verify AUR package {package}: network failure ({error})") from error

    def install(self, packages: list[str]) -> None:
        if not packages:
            return
        args = ["yay", "-S", "--needed", "--noconfirm"] + packages
        self._exec.execute(args, step="install:yay")
