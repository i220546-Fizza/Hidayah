from sqlalchemy import select, text

from app.models import AuditEvent, Bookmark, Conversation, Message, User, UserSession
from app.models.enums import MessageRole
from tests.factories import make_verse
from tests.helpers import GOOD_PASSWORD, login, make_admin, register, signup_and_login


def auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ---------- Profile and preferences ----------

def test_update_display_name(client):
    headers, _ = signup_and_login(client)
    r = client.patch("/api/v1/users/me", headers=headers, json={"display_name": "  Fatima  "})
    assert r.status_code == 200 and r.json()["display_name"] == "Fatima"


def test_preferences_have_safe_defaults_reminders_off(client):
    headers, _ = signup_and_login(client)
    p = client.get("/api/v1/users/me/preferences", headers=headers).json()
    assert p == {"language": "en", "arabic_font_size": 28, "reminders_enabled": False, "reminder_time": None}


def test_update_preferences_persists(client):
    headers, _ = signup_and_login(client)
    r = client.put("/api/v1/users/me/preferences", headers=headers,
                   json={"language": "ur", "arabic_font_size": 36, "reminders_enabled": True, "reminder_time": "06:30:00"})
    assert r.status_code == 200
    again = client.get("/api/v1/users/me/preferences", headers=headers).json()
    assert again["language"] == "ur" and again["arabic_font_size"] == 36 and again["reminder_time"] == "06:30:00"


def test_preferences_validation(client):
    headers, _ = signup_and_login(client)
    put = lambda body: client.put("/api/v1/users/me/preferences", headers=headers, json=body).status_code
    assert put({"language": "fr"}) == 422
    assert put({"arabic_font_size": 5}) == 422
    assert put({"arabic_font_size": 500}) == 422
    # consent: reminders cannot be enabled without choosing a time
    assert put({"reminders_enabled": True}) == 422
    assert client.get("/api/v1/users/me/preferences", headers=headers).json()["reminders_enabled"] is False


# ---------- Password change ----------

def test_change_password_requires_current_password(client):
    headers, _ = signup_and_login(client)
    r = client.post("/api/v1/users/me/password", headers=headers,
                    json={"current_password": "wrong-password-1", "new_password": "a-brand-new-password"})
    assert r.status_code == 401


def test_change_password_enforces_policy(client):
    headers, _ = signup_and_login(client)
    r = client.post("/api/v1/users/me/password", headers=headers,
                    json={"current_password": GOOD_PASSWORD, "new_password": "short"})
    assert r.status_code == 422


def test_change_password_signs_out_other_devices_but_not_this_one(client):
    headers, _ = signup_and_login(client)
    other = auth(login(client).json())
    r = client.post("/api/v1/users/me/password", headers=headers,
                    json={"current_password": GOOD_PASSWORD, "new_password": "a-brand-new-password"})
    assert r.status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    assert client.get("/api/v1/users/me", headers=other).status_code == 401
    assert login(client, password=GOOD_PASSWORD).status_code == 401
    assert login(client, password="a-brand-new-password").status_code == 200


# ---------- Export ----------

def test_export_contains_user_data_and_no_secrets(client, session):
    headers, _ = signup_and_login(client)
    verse = make_verse(session)
    client.post("/api/v1/bookmarks", headers=headers, json={"type": "verse", "target_id": verse.id})
    user = session.scalar(select(User))
    conv = Conversation(user_id=user.id, title="Test chat")
    session.add(conv)
    session.flush()
    session.add(Message(conversation_id=conv.id, role=MessageRole.USER, content="hello"))
    session.commit()

    r = client.get("/api/v1/users/me/export", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["profile"]["email"] == "user@example.com"
    assert data["bookmarks"][0]["type"] == "verse"
    assert data["conversations"][0]["messages"][0]["content"] == "hello"
    text_ = r.text.lower()
    assert "argon2" not in text_ and "password_hash" not in text_
    assert "refresh_token" not in text_ and "access_token" not in text_


def test_export_only_includes_the_callers_data(client, session):
    a, _ = signup_and_login(client, "a@example.com")
    b, _ = signup_and_login(client, "b@example.com")
    verse = make_verse(session)
    client.post("/api/v1/bookmarks", headers=a, json={"type": "verse", "target_id": verse.id})
    assert client.get("/api/v1/users/me/export", headers=b).json()["bookmarks"] == []


# ---------- Account deletion ----------

def test_delete_account_requires_correct_password(client):
    headers, _ = signup_and_login(client)
    assert client.post("/api/v1/users/me/delete", headers=headers, json={"password": "wrong-password-1"}).status_code == 401
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


def test_delete_account_removes_all_personal_data(client, session):
    headers, _ = signup_and_login(client)
    verse = make_verse(session)
    client.post("/api/v1/bookmarks", headers=headers, json={"type": "verse", "target_id": verse.id})
    uid = session.scalar(select(User.id))
    session.add(Conversation(user_id=uid, title="private"))
    session.commit()

    assert client.post("/api/v1/users/me/delete", headers=headers, json={"password": GOOD_PASSWORD}).status_code == 204

    for table in ("users", "auth_identities", "sessions", "bookmarks", "conversations", "user_preferences"):
        assert session.scalar(text(f"select count(*) from {table}")) == 0, table
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert login(client).status_code == 401
    event = session.scalar(select(AuditEvent).where(AuditEvent.action == "account_deleted"))
    assert event is not None and event.actor_id is None
    assert "example.com" not in str(event.entity_id) and "example.com" not in str(event.details)


def test_only_administrator_cannot_delete_their_account(client, session):
    headers, _ = signup_and_login(client)
    make_admin(session, "user@example.com")
    r = client.post("/api/v1/users/me/delete", headers=headers, json={"password": GOOD_PASSWORD})
    assert r.status_code == 409
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


def test_deleted_users_sessions_are_gone(client, session):
    headers, tokens = signup_and_login(client)
    client.post("/api/v1/users/me/delete", headers=headers, json={"password": GOOD_PASSWORD})
    assert session.scalar(select(UserSession)) is None
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
