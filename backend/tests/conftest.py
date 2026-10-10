"""
Test setup. Tests run against a REAL PostgreSQL database with pgvector, and the schema
is created by running the Alembic migrations (not by metadata.create_all), so the
migrations themselves are tested.

Set TEST_DATABASE_URL to point at a throwaway database server. The database named in the
URL is dropped and recreated for each test session, so never point it at real data.
"""
import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://hidayah:change-me@localhost:5432/hidayah_test",
)

# Make the whole app (including Alembic's env.py) use the test database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENV"] = "test"
# 32+ characters so the JWT library does not warn; real deployments set their own secret.
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-automated-tests-0123456789")


def _alembic_config() -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option(
        "script_location", os.path.join(os.path.dirname(__file__), "..", "migrations")
    )
    return cfg


def _recreate_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    name = url.database
    assert name and name.endswith("_test"), "refusing to drop a database not ending in _test"
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def migrated_engine() -> Iterator[Engine]:
    _recreate_database()
    from app.core.config import get_settings

    get_settings.cache_clear()
    command.upgrade(_alembic_config(), "head")
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def alembic_cfg() -> Config:
    return _alembic_config()


@pytest.fixture
def session(migrated_engine: Engine) -> Iterator[Session]:
    """A session inside a transaction that is rolled back after every test."""
    connection = migrated_engine.connect()
    transaction = connection.begin()
    # create_savepoint: code under test may call commit(); it only releases a savepoint,
    # so everything is still rolled back at the end of the test.
    db = Session(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.security.rate_limit import limiter

    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def client(session: Session):
    """HTTP client whose requests use the per-test database session."""
    from fastapi.testclient import TestClient

    from app.db.session import get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as c:
        yield c
