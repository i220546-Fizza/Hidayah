"""Command-line tools. Usage:  python -m app.cli create-admin --email you@example.com  |  python -m app.cli check-db"""
import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import make_engine
from app.services.users import bootstrap_admin


def create_admin(email: str) -> int:
    # The password is typed here, hidden, and never passed on the command line or logged.
    password = getpass.getpass("Password for the administrator: ")
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.", file=sys.stderr)
        return 1
    with Session(make_engine()) as db:
        try:
            user = bootstrap_admin(db, email, password)
        except AppError as exc:
            print(f"Could not create administrator: {exc.message} {exc.errors or ''}", file=sys.stderr)
            return 1
    print(f"{user.email} is now an administrator.")
    return 0


def check_db() -> int:
    """Show which database we are using (never the password) and whether it works."""
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    engine = make_engine()
    url = engine.url
    print(f"Trying: user={url.username} host={url.host} port={url.port} database={url.database}")
    try:
        with engine.connect() as conn:
            who = conn.execute(text("select current_user, current_database()")).one()
            version = conn.execute(text("show server_version")).scalar_one()
            vector = conn.execute(
                text("select extversion from pg_extension where extname = 'vector'")
            ).scalar_one_or_none()
            has_table = conn.execute(text("select to_regclass('public.alembic_version')")).scalar_one()
            applied = (
                conn.execute(text("select version_num from alembic_version")).scalar_one_or_none()
                if has_table
                else None
            )
    except OperationalError as exc:
        reason = str(exc.orig).strip()
        print(f"FAILED: {reason}", file=sys.stderr)
        if "role" in reason and "does not exist" in reason:
            print(
                "Hint: a different PostgreSQL is answering on this port. Make the port in "
                "DATABASE_URL match HIDAYAH_DB_PORT (default 5433).",
                file=sys.stderr,
            )
        elif "password authentication failed" in reason:
            print(
                "Hint: an existing volume keeps the password it was created with; changing "
                "POSTGRES_PASSWORD later does not change it. Use the original password.",
                file=sys.stderr,
            )
        return 1
    print(f"OK: connected as {who[0]} to {who[1]} (PostgreSQL {version})")
    print(f"pgvector extension: {vector or 'not installed yet (migration 0001 installs it)'}")
    print(f"migration applied: {applied or 'none yet'}")
    return 0


def import_file_cmd(args) -> int:
    """Import a local file as a new version of a registered source (same licence gate as the API)."""
    from pathlib import Path

    from app.ingest.service import import_file
    from app.services import sources as sources_service

    path = Path(args.path)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    with Session(make_engine()) as db:
        try:
            source = sources_service.get(db, args.source_id)
            result = import_file(
                db, None, source, kind=args.kind, raw=path.read_bytes(), filename=path.name,
                version_label=args.version_label, language=args.language,
                collection_slug=args.collection_slug, collection_name=args.collection_name,
            )
        except AppError as exc:
            print(f"Import refused: {exc.message}", file=sys.stderr)
            for line in exc.errors or []:
                print(f"  - {line}", file=sys.stderr)
            return 1
    print("Nothing changed (same file already imported)." if result.unchanged else f"Imported: {result.counts}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="Create (or promote) an administrator account")
    p.add_argument("--email", required=True)
    sub.add_parser("check-db", help="Test the database connection and show migration status")
    i = sub.add_parser("import-file", help="Import a file as a new version of a registered source")
    i.add_argument("--source-id", type=int, required=True)
    i.add_argument("--kind", required=True)
    i.add_argument("--version-label", required=True)
    i.add_argument("--language")
    i.add_argument("--collection-slug")
    i.add_argument("--collection-name")
    i.add_argument("path")
    args = parser.parse_args()
    if args.command == "check-db":
        return check_db()
    if args.command == "import-file":
        return import_file_cmd(args)
    return create_admin(args.email)


if __name__ == "__main__":
    raise SystemExit(main())
