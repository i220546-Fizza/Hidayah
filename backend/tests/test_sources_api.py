"""Source registry API: admin only, and 'approved' can only be reached through the licence gate."""
import pytest

from tests.factories import make_version
from tests.helpers import make_admin, signup_and_login

NEW = {"slug": "test-quran-text", "title": "Test Quran text", "category": "quran_text", "language": "ar"}
FULL_RIGHTS = {
    "rights_holder": "Test Foundation", "license_name": "Test Licence 1.0",
    "commercial_use": "allowed", "storage_permission": "allowed",
    "indexing_permission": "allowed", "rag_permission": "allowed",
}


@pytest.fixture
def admin(client, session):
    headers, _ = signup_and_login(client, "admin@example.com")
    make_admin(session, "admin@example.com")
    return headers


def _create(client, admin, **over):
    r = client.post("/api/v1/admin/sources", json={**NEW, **over}, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def _approve_path(client, session, admin, source):
    sid = source["id"]
    assert client.patch(f"/api/v1/admin/sources/{sid}/rights", json=FULL_RIGHTS, headers=admin).status_code == 200
    assert client.post(f"/api/v1/admin/sources/{sid}/verify-licence", json={"note": "read the page"}, headers=admin).status_code == 200
    from app.models import Source
    make_version(session, session.get(Source, sid))
    assert client.post(f"/api/v1/admin/sources/{sid}/verify-content", json={"note": "checked"}, headers=admin).status_code == 200
    return client.post(f"/api/v1/admin/sources/{sid}/status", json={"to_status": "approved", "note": "all checks done"}, headers=admin)


def test_admin_routes_require_admin(client):
    assert client.get("/api/v1/admin/sources").status_code == 401
    headers, _ = signup_and_login(client, "plain@example.com")
    for method, path in [("get", "/admin/sources"), ("post", "/admin/sources"), ("get", "/admin/audit")]:
        r = getattr(client, method)(f"/api/v1{path}", headers=headers, **({"json": NEW} if method == "post" else {}))
        assert r.status_code == 403, path


def test_new_source_starts_as_draft_with_unknown_rights(client, admin):
    s = _create(client, admin)
    assert s["approval_status"] == "draft"
    for f in ("commercial_use", "storage_permission", "indexing_permission", "rag_permission"):
        assert s[f] == "unknown"


def test_duplicate_slug_is_a_conflict(client, admin):
    _create(client, admin)
    assert client.post("/api/v1/admin/sources", json=NEW, headers=admin).status_code == 409


def test_bad_slug_rejected(client, admin):
    assert client.post("/api/v1/admin/sources", json={**NEW, "slug": "Bad Slug!"}, headers=admin).status_code == 422


def test_cannot_approve_and_reasons_are_explained(client, admin):
    s = _create(client, admin)
    r = client.post(f"/api/v1/admin/sources/{s['id']}/status", json={"to_status": "approved", "note": "try"}, headers=admin)
    assert r.status_code == 422
    errors = " ".join(r.json()["errors"])
    for phrase in ("who holds the rights", "licence name", "verify the licence", "permanent storage",
                   "search indexing", "answer-assistant retrieval", "commercial use", "verify the content"):
        assert phrase in errors
    ready = client.get(f"/api/v1/admin/sources/{s['id']}/readiness", headers=admin).json()
    assert ready["ready"] is False and len(ready["missing"]) >= 7


def test_licence_cannot_be_verified_without_holder_and_name(client, admin):
    s = _create(client, admin)
    r = client.post(f"/api/v1/admin/sources/{s['id']}/verify-licence", json={"note": "no data"}, headers=admin)
    assert r.status_code == 422


def test_content_cannot_be_verified_before_an_import_exists(client, admin):
    s = _create(client, admin)
    r = client.post(f"/api/v1/admin/sources/{s['id']}/verify-content", json={"note": "nothing to check"}, headers=admin)
    assert r.status_code == 422


def test_each_unmet_permission_blocks_approval(client, session, admin):
    for i, field in enumerate(("commercial_use", "storage_permission", "indexing_permission", "rag_permission")):
        s = _create(client, admin, slug=f"blocked-{i}")
        rights = {**FULL_RIGHTS, field: "requires_permission"}
        client.patch(f"/api/v1/admin/sources/{s['id']}/rights", json=rights, headers=admin)
        client.post(f"/api/v1/admin/sources/{s['id']}/verify-licence", json={"note": "x1"}, headers=admin)
        from app.models import Source
        make_version(session, session.get(Source, s["id"]))
        client.post(f"/api/v1/admin/sources/{s['id']}/verify-content", json={"note": "x2"}, headers=admin)
        r = client.post(f"/api/v1/admin/sources/{s['id']}/status", json={"to_status": "approved", "note": "no"}, headers=admin)
        assert r.status_code == 422, field


def test_full_path_to_approval_and_public_credit(client, session, admin):
    s = _create(client, admin, author_or_publisher="Test Author", edition="v1")
    client.patch(f"/api/v1/admin/sources/{s['id']}/rights", json={"attribution_text": "Text: Test Foundation"}, headers=admin)
    assert client.get("/api/v1/sources").json() == []  # nothing public yet
    r = _approve_path(client, session, admin, s)
    assert r.status_code == 200, r.text
    assert r.json()["approval_status"] == "approved"
    public = client.get("/api/v1/sources").json()
    assert [p["slug"] for p in public] == ["test-quran-text"]
    assert public[0]["attribution_text"] == "Text: Test Foundation"
    assert "license_verified_by" not in public[0] and "rights_notes" not in public[0]


def test_unapproved_sources_are_never_public(client, session, admin):
    s = _create(client, admin)
    client.post(f"/api/v1/admin/sources/{s['id']}/status", json={"to_status": "candidate", "note": "chosen"}, headers=admin)
    assert client.get("/api/v1/sources").json() == []


def test_changing_rights_of_an_approved_source_sends_it_back_to_review(client, session, admin):
    s = _create(client, admin)
    assert _approve_path(client, session, admin, s).status_code == 200
    r = client.patch(f"/api/v1/admin/sources/{s['id']}/rights", json={"rag_permission": "unknown"}, headers=admin)
    body = r.json()
    assert body["approval_status"] == "under_review"
    assert body["license_verified_at"] is None
    assert client.get("/api/v1/sources").json() == []


def test_unchanged_rights_do_not_revoke_approval(client, session, admin):
    s = _create(client, admin)
    assert _approve_path(client, session, admin, s).status_code == 200
    r = client.patch(f"/api/v1/admin/sources/{s['id']}/rights", json={"rag_permission": "allowed"}, headers=admin)
    assert r.json()["approval_status"] == "approved"


def test_status_change_is_logged_with_reviewer_and_note(client, session, admin):
    s = _create(client, admin)
    client.post(f"/api/v1/admin/sources/{s['id']}/status", json={"to_status": "pending_permission", "note": "asked the publisher"}, headers=admin)
    reviews = client.get(f"/api/v1/admin/sources/{s['id']}/reviews", headers=admin).json()
    assert reviews[0]["from_status"] == "draft" and reviews[0]["to_status"] == "pending_permission"
    assert reviews[0]["note"] == "asked the publisher" and reviews[0]["reviewer_id"]
    actions = [e["action"] for e in client.get("/api/v1/admin/audit", headers=admin).json()["items"]]
    assert "source_status_changed" in actions and "source_created" in actions


def test_same_status_is_rejected(client, admin):
    s = _create(client, admin)
    r = client.post(f"/api/v1/admin/sources/{s['id']}/status", json={"to_status": "draft", "note": "same"}, headers=admin)
    assert r.status_code == 422


def test_listing_can_filter_by_status(client, admin):
    a = _create(client, admin, slug="one-a")
    _create(client, admin, slug="two-b")
    client.post(f"/api/v1/admin/sources/{a['id']}/status", json={"to_status": "restricted", "note": "terms conflict"}, headers=admin)
    r = client.get("/api/v1/admin/sources?status=restricted", headers=admin).json()
    assert r["total"] == 1 and r["items"][0]["slug"] == "one-a"


def test_unknown_source_is_404(client, admin):
    assert client.get("/api/v1/admin/sources/999999", headers=admin).status_code == 404
