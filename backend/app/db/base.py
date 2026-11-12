from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Parent of every ORM model; its metadata is what Alembic compares against the database."""
