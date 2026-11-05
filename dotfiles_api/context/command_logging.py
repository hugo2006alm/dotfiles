import re
import shlex
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit


def redacted_diagnostics(args: list[str], diagnostic: str = "", *,
                         sensitive: bool = False) -> tuple[str, str]:
    """Default-deny private launch/clipboard/scripts; redact credentials elsewhere.

    Output is for observability only. Original argv and stdout remain available
    to the executor/caller and must never be printed as diagnostics.
    """
    executable = Path(args[0]).name if args else "command"
    private_tools = {"wl-paste", "wl-copy", "xclip", "xsel", "zen", "zen-browser",
                     "firefox", "chromium", "google-chrome", "brave", "sh", "bash", "dash",
                     "zsh", "fish", "ksh", "pwsh", "powershell"}
    scripts = any(flag in args[1:] for flag in ("-c", "-lc", "-ec", "-xc", "-Command"))
    headers = any(re.search(r"(?i)\b(?:proxy-)?authorization\s*:", arg) for arg in args)
    if sensitive or executable in private_tools or scripts or headers:
        return (f"{shlex.quote(executable)} [arguments redacted]",
                "[private diagnostic redacted]" if diagnostic else "")

    flags = {"--password", "--token", "--api-key", "--secret", "--client-secret"}
    safe, secrets = list(args), []
    url_pattern = r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s'\"<>]+"
    contains_url = any(re.search(url_pattern, argument) for argument in args)
    for index, argument in enumerate(args):
        if index and args[index - 1].lower() in flags:
            secrets.append(argument)
            safe[index] = "[REDACTED]"
        elif "=" in argument and argument.split("=", 1)[0].lower() in flags:
            key, value = argument.split("=", 1)
            secrets.append(value)
            safe[index] = key + "=[REDACTED]"
        for url in re.findall(url_pattern, argument):
            secrets.append(url)
            try:
                parsed = urlsplit(url)
                secrets.extend(value for _, value in parse_qsl(parsed.query, keep_blank_values=True))
                secrets.extend(value for value in (parsed.username, parsed.password, parsed.fragment) if value)
            except ValueError:
                # Malformed URLs still get completely removed below.
                pass

    def redact(value: str) -> str:
        for secret in sorted(set(secrets), key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[REDACTED]").replace(unquote(secret), "[REDACTED]")
        value = re.sub(url_pattern, "[URL REDACTED]", value)
        value = re.sub(r"(?im)\b(?:proxy-)?authorization\s*:[^\r\n]*", "Authorization: [REDACTED]", value)
        value = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)", "[REDACTED]", value)
        value = re.sub(r"(?i)(--(?:password|token|api-key|secret|client-secret)(?:=|\s+))[^\s'\"]+", r"\1[REDACTED]", value)
        return value

    # URL consumers can echo opaque callback/path/fragment tokens without the
    # surrounding URL. Heuristics cannot identify every such value safely.
    diagnostic = "[URL diagnostic redacted]" if contains_url and diagnostic else redact(diagnostic)[:2000]
    return redact(shlex.join(safe)), diagnostic
