from pathlib import Path
from dotfiles_api.domain.contracts import FileWriter

class SystemFileWriter(FileWriter):
    def write(self, target_path: Path, content: str) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)
