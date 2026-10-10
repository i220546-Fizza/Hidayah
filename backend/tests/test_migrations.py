from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.db.base import Base


def test_all_model_tables_exist_after_upgrade(migrated_engine):
    existing = set(inspect(migrated_engine).get_table_names())
    expected = set(Base.metadata.tables)
    assert expected <= existing
    assert len(expected) == 42


def test_models_match_migrations_with_no_drift(migrated_engine):
    """If this fails, a model changed without a new migration."""
    with migrated_engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata)
    assert diff == []


def test_pgvector_extension_installed(migrated_engine):
    with migrated_engine.connect() as conn:
        version = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar()
    assert version is not None


def test_roles_are_seeded(migrated_engine):
    with migrated_engine.connect() as conn:
        names = {r[0] for r in conn.execute(text("SELECT name FROM roles"))}
    assert names == {"user", "editor", "admin"}


def test_no_content_is_seeded(migrated_engine):
    """Migrations must never insert Islamic content or fake records."""
    with migrated_engine.connect() as conn:
        for table in ("sources", "surahs", "verses", "hadith_records", "duas", "users"):
            assert conn.execute(text(f"SELECT count(*) FROM {table}")).scalar() == 0, table


def test_downgrade_then_upgrade_round_trip(migrated_engine, alembic_cfg):
    command.downgrade(alembic_cfg, "base")
    remaining = set(inspect(migrated_engine).get_table_names()) - {"alembic_version"}
    assert remaining == set()
    command.upgrade(alembic_cfg, "head")
    assert len(set(inspect(migrated_engine).get_table_names()) & set(Base.metadata.tables)) == 42
