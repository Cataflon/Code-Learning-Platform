"""Maintenance commands. Usage: ``python -m app.cli reindex-materials``."""

import sys

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models import Material
from app.services.material_service import extract_pages
from app.storage.file_store import get_file_store


def reindex_materials() -> None:
    """Extract the page text of every material (needed once for files uploaded before Step 9)."""
    store = get_file_store()
    with get_session_factory()() as db:
        for material in db.scalars(select(Material).order_by(Material.id)):
            pages = extract_pages(db, material, store)
            print(
                f"{material.id:>4}  {material.title}: "
                f"{pages} of {material.page_count} pages with text"
            )


COMMANDS = {"reindex-materials": reindex_materials}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print(f"Usage: python -m app.cli {{{'|'.join(COMMANDS)}}}")
        return 2
    COMMANDS[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
