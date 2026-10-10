"""Command-line tools. Usage:  python -m app.cli create-admin --email you@example.com"""
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


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="Create (or promote) an administrator account")
    p.add_argument("--email", required=True)
    args = parser.parse_args()
    return create_admin(args.email) if args.command == "create-admin" else 2


if __name__ == "__main__":
    raise SystemExit(main())
