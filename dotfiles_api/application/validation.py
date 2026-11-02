import configparser
import json
import re
import tomllib
from pathlib import Path


class ArtifactValidator:
    """Pure format checks; application-specific compiler checks remain separate."""

    def validate(self, path: Path, content: str) -> None:
        if "\x00" in content:
            raise ValueError(f"NUL byte in generated artifact: {path}")
        if path.suffix == ".json":
            json.loads(content)
        elif path.suffix == ".toml":
            tomllib.loads(content)
        elif path.suffix == ".ini":
            configparser.ConfigParser(interpolation=None).read_string(content)
        elif path.suffix in {".css", ".scss"}:
            text = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
            stack, quote, escaped = [], None, False
            for character in text:
                if quote:
                    if escaped:
                        escaped = False
                    elif character == "\\":
                        escaped = True
                    elif character == quote:
                        quote = None
                elif character in {"'", '"'}:
                    quote = character
                elif character in "({[":
                    stack.append(character)
                elif character in ")}]":
                    if not stack or stack.pop() != {")": "(", "}": "{", "]": "["}[character]:
                        raise ValueError(f"Unbalanced stylesheet: {path}")
            if stack or quote:
                raise ValueError(f"Incomplete stylesheet: {path}")
