"""The migrations must build the schema from an empty database and take it back down."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from tests.conftest import database_url, ensure_database

MIGRATION_DATABASE = "autograder_migration_test"
BACKEND_DIR = Path(__file__).resolve().parents[2]


def test_migrations_upgrade_from_empty_database_and_downgrade():
    ensure_database(MIGRATION_DATABASE, recreate=True)
    url = database_url(MIGRATION_DATABASE).render_as_string(hide_password=False)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    config.attributes["configure_logging"] = False
    engine = create_engine(url)

    command.upgrade(config, "head")
    tables_after_upgrade = set(inspect(engine).get_table_names())
    # Fails if the models have changes that no migration covers.
    command.check(config)
    command.downgrade(config, "base")
    tables_after_downgrade = set(inspect(engine).get_table_names())
    engine.dispose()

    assert {"users", "courses", "assignments", "test_cases"} <= tables_after_upgrade
    assert tables_after_downgrade == {"alembic_version"}
