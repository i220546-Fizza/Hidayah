"""Helpers for API tests."""
GOOD_PASSWORD = "correct-horse-battery"
WEB = {"X-Hidayah-Client": "web"}


def register(client, email="user@example.com", password=GOOD_PASSWORD, **extra):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password, **extra})


def login(client, email="user@example.com", password=GOOD_PASSWORD, headers=None):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}, headers=headers or {})


def signup_and_login(client, email="user@example.com", password=GOOD_PASSWORD):
    """Register + log in (mobile style). Returns (auth_headers, tokens_json)."""
    assert register(client, email, password).status_code == 201
    r = login(client, email, password)
    assert r.status_code == 200, r.text
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}, tokens


def make_admin(session, email):
    from sqlalchemy import select

    from app.models import Role, User

    user = session.scalar(select(User).where(User.email == email))
    user.roles.append(session.scalar(select(Role).where(Role.name == "admin")))
    session.commit()
