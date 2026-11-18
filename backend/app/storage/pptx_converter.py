"""PPTX to PDF with LibreOffice in headless mode (decision D20).

``soffice --headless --convert-to pdf --outdir <dir> <file>`` with a profile folder of its own
(``-env:UserInstallation``), so a conversion never depends on, or damages, a user's profile.
One conversion at a time and a timeout, so a hostile or huge presentation cannot hold the
server. Tests replace the converter with a fake one through ``get_converter``.
"""

import os
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from app.core.config import get_settings

_one_at_a_time = threading.Lock()

Converter = Callable[[Path, Path], Path]

_WINDOWS_PATHS = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)


class ConversionError(Exception):
    """The presentation could not be converted (or LibreOffice is not installed)."""


def find_soffice() -> str | None:
    configured = get_settings().soffice_path
    if configured:
        return configured if Path(configured).is_file() else None
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    return next((path for path in _WINDOWS_PATHS if Path(path).is_file()), None)


def convert_pptx_to_pdf(src: Path, dst_dir: Path) -> Path:
    """Convert ``src`` and return the path of the PDF written into ``dst_dir``."""
    soffice = find_soffice()
    if soffice is None:
        raise ConversionError("LibreOffice is not installed on the server")
    timeout = get_settings().pptx_convert_timeout_s
    with _one_at_a_time, tempfile.TemporaryDirectory(prefix="lo-profile-") as profile:
        command = [
            soffice,
            f"-env:UserInstallation={Path(profile).as_uri()}",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(dst_dir),
            str(src),
        ]
        try:
            subprocess.run(
                command,
                capture_output=True,
                timeout=timeout,
                check=True,
                env={**os.environ, "HOME": profile},
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversionError("The conversion took too long") from exc
        except (subprocess.CalledProcessError, OSError) as exc:
            raise ConversionError("LibreOffice could not convert the file") from exc
    result = dst_dir / f"{src.stem}.pdf"
    if not result.is_file():
        raise ConversionError("LibreOffice did not produce a PDF")
    return result


def get_converter() -> Converter:
    """FastAPI dependency."""
    return convert_pptx_to_pdf
