"""Maintenance commands.

Usage:
    python -m app.cli reindex-materials
    python -m app.cli create-admin EMAIL "FULL NAME"   (asks for the password, or reads
                                                        ADMIN_PASSWORD from the environment)
"""

import getpass
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models import Material, Role, User
from app.schemas.auth import MIN_PASSWORD_LENGTH
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


def create_admin(email: str, full_name: str) -> int:
    """The first admin cannot register from the site (D30): it is made here."""
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"The password needs at least {MIN_PASSWORD_LENGTH} characters.")
        return 1
    email = email.strip().lower()
    with get_session_factory()() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name=full_name.strip(), role=Role.admin, password_hash="")
            db.add(user)
        user.role = Role.admin
        user.is_active = True
        user.password_hash = hash_password(password)
        db.commit()
    print(f"Admin ready: {email}")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["reindex-materials"]:
        reindex_materials()
        return 0
    if len(argv) == 3 and argv[0] == "create-admin":
        return create_admin(argv[1], argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
