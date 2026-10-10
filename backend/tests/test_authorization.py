"""Roles are enforced on the server for every admin endpoint."""
import uuid

import pytest
from sqlalchemy import select

from app.models import AuditEvent, Role, User
from tests.helpers import make_admin, signup_and_login

ADMIN_ENDPOINTS = [
    ("get", "/api/v1/admin/users", None),
    ("post", f"/api/v1/admin/users/{uuid.uuid4()}/roles", {"role": "editor"}),
    ("delete", f"/api/v1/admin/users/{uuid.uuid4()}/roles/editor", None),
]


def call(client, method, url, body, headers=None):
    kwargs = {"headers": headers or {}}
    if body is not None:
        kwargs["json"] = body
    return getattr(client, method)(url, **kwargs)


@pytest.mark.parametrize("method,url,body", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_anonymous(client, method, url, body):
    assert call(client, method, url, body).status_code == 401


@pytest.mark.parametrize("method,url,body", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_normal_users(client, method, url, body):
    headers, _ = signup_and_login(client)
    assert call(client, method, url, body, headers).status_code == 403


@pytest.mark.parametrize("method,url,body", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_editors(client, session, method, url, body):
    headers, _ = signup_and_login(client)
    user = session.scalar(select(User))
    user.roles.append(session.scalar(select(Role).where(Role.name == "editor")))
    session.commit()
    assert call(client, method, url, body, headers).status_code == 403


def test_admin_can_list_users_with_pagination(client, session):
    admin_h, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    for i in range(3):
        signup_and_login(client, f"u{i}@example.com")
    page = client.get("/api/v1/admin/users", headers=admin_h, params={"limit": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert client.get("/api/v1/admin/users", headers=admin_h, params={"limit": 1000}).status_code == 422


def test_role_is_checked_on_each_request_not_cached_in_the_token(client, session):
    headers, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 200
    user = session.scalar(select(User))
    user.roles.remove(session.scalar(select(Role).where(Role.name == "admin")))
    session.commit()
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403


def test_user_cannot_grant_themselves_admin(client, session):
    headers, _ = signup_and_login(client)
    uid = session.scalar(select(User.id))
    r = client.post(f"/api/v1/admin/users/{uid}/roles", headers=headers, json={"role": "admin"})
    assert r.status_code == 403
    assert "admin" not in client.get("/api/v1/users/me", headers=headers).json()["roles"]


def test_admin_grants_and_revokes_roles_with_audit_trail(client, session):
    admin_h, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    signup_and_login(client, "ed@example.com")
    ed_id = session.scalar(select(User.id).where(User.email == "ed@example.com"))

    r = client.post(f"/api/v1/admin/users/{ed_id}/roles", headers=admin_h, json={"role": "editor"})
    assert r.status_code == 200 and r.json()["roles"] == ["editor", "user"]
    r = client.delete(f"/api/v1/admin/users/{ed_id}/roles/editor", headers=admin_h)
    assert r.status_code == 200 and r.json()["roles"] == ["user"]

    events = session.scalars(select(AuditEvent).where(AuditEvent.entity_id == str(ed_id)).order_by(AuditEvent.id)).all()
    assert [e.action for e in events] == ["role_granted", "role_revoked"]
    assert all(e.actor_id is not None and e.details == {"role": "editor"} for e in events)


def test_cannot_remove_last_administrator_or_base_role(client, session):
    admin_h, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    aid = session.scalar(select(User.id))
    assert client.delete(f"/api/v1/admin/users/{aid}/roles/admin", headers=admin_h).status_code == 409
    assert client.delete(f"/api/v1/admin/users/{aid}/roles/user", headers=admin_h).status_code == 403


def test_unknown_user_or_role_is_404_or_422(client, session):
    admin_h, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    assert client.post(f"/api/v1/admin/users/{uuid.uuid4()}/roles", headers=admin_h, json={"role": "editor"}).status_code == 404
    aid = session.scalar(select(User.id))
    assert client.post(f"/api/v1/admin/users/{aid}/roles", headers=admin_h, json={"role": "superuser"}).status_code == 422
    assert client.delete(f"/api/v1/admin/users/{aid}/roles/nonexistent", headers=admin_h).status_code == 404


def test_cli_bootstrap_creates_admin(session):
    from app.services.users import bootstrap_admin

    user = bootstrap_admin(session, "Boss@Example.com", "a-long-enough-password")
    assert user.email == "boss@example.com"
    assert sorted(r.name for r in user.roles) == ["admin", "user"]
    again = bootstrap_admin(session, "boss@example.com", "ignored-because-exists")
    assert again.id == user.id and sorted(r.name for r in again.roles) == ["admin", "user"]
