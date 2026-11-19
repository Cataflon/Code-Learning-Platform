"""The only code that touches the uploads/ folder.

Names on disk are always generated here (uuid4 + extension). Nothing that comes from a
client, neither a file name nor a title, is ever used to build a path.
"""

import contextlib
import re
import shutil
import uuid
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

_NAME = re.compile(r"^[0-9a-f]{32}\.(pdf|pptx)$")


class FileStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, name: str) -> Path:
        # Defence in depth: only names this class generated are accepted.
        if not _NAME.fullmatch(name):
            raise ValueError(f"Invalid stored file name: {name!r}")
        return self.root / name

    def new_name(self, extension: str) -> str:
        return f"{uuid.uuid4().hex}.{extension}"

    def save_file(self, source: Path, extension: str) -> str:
        """Move a finished temporary file into the store and return its new name."""
        self.root.mkdir(parents=True, exist_ok=True)
        name = self.new_name(extension)
        shutil.move(str(source), self._path(name))
        return name

    def path(self, name: str) -> Path:
        """Where a stored file is, for serving it."""
        return self._path(name)

    def delete(self, name: str) -> None:
        """Remove a stored file; a file that is already gone is not an error."""
        with contextlib.suppress(FileNotFoundError):
            self._path(name).unlink()

    def temp_dir(self) -> Path:
        """A scratch folder next to the store, so moving files out of it is cheap."""
        folder = self.root / ".tmp"
        folder.mkdir(parents=True, exist_ok=True)
        return folder


@lru_cache
def get_file_store() -> FileStore:
    """FastAPI dependency; tests point it at a temporary folder."""
    return FileStore(get_settings().upload_dir)
