import pytest

from tests.factories import make_dua, make_hadith, make_verse
from tests.helpers import signup_and_login

URL = "/api/v1/bookmarks"


def test_all_endpoints_require_login(client):
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"type": "verse", "target_id": 1}).status_code == 401
    assert client.delete(f"{URL}/1").status_code == 401


@pytest.mark.parametrize("kind,maker", [("verse", make_verse), ("hadith", make_hadith), ("dua", make_dua)])
def test_create_and_list_each_type(client, session, kind, maker):
    headers, _ = signup_and_login(client)
    target = maker(session)
    r = client.post(URL, headers=headers, json={"type": kind, "target_id": target.id})
    assert r.status_code == 201
    assert r.json()["type"] == kind and r.json()["target_id"] == target.id
    listed = client.get(URL, headers=headers).json()
    assert listed["total"] == 1 and listed["items"][0]["type"] == kind


def test_bookmark_of_missing_target_is_404(client):
    headers, _ = signup_and_login(client)
    assert client.post(URL, headers=headers, json={"type": "verse", "target_id": 999999}).status_code == 404


def test_duplicate_bookmark_is_conflict(client, session):
    headers, _ = signup_and_login(client)
    v = make_verse(session)
    assert client.post(URL, headers=headers, json={"type": "verse", "target_id": v.id}).status_code == 201
    assert client.post(URL, headers=headers, json={"type": "verse", "target_id": v.id}).status_code == 409


def test_invalid_input_rejected(client):
    headers, _ = signup_and_login(client)
    assert client.post(URL, headers=headers, json={"type": "book", "target_id": 1}).status_code == 422
    assert client.post(URL, headers=headers, json={"type": "verse"}).status_code == 422
    assert client.get(URL, headers=headers, params={"limit": 0}).status_code == 422
    assert client.get(URL, headers=headers, params={"limit": 101}).status_code == 422
    assert client.get(URL, headers=headers, params={"offset": -1}).status_code == 422


def test_pagination_filter_and_order(client, session):
    headers, _ = signup_and_login(client)
    verses = [make_verse(session, verse=i) for i in range(1, 6)]
    for v in verses:
        client.post(URL, headers=headers, json={"type": "verse", "target_id": v.id})
    client.post(URL, headers=headers, json={"type": "dua", "target_id": make_dua(session).id})

    page1 = client.get(URL, headers=headers, params={"limit": 4}).json()
    page2 = client.get(URL, headers=headers, params={"limit": 4, "offset": 4}).json()
    assert page1["total"] == 6 and len(page1["items"]) == 4 and len(page2["items"]) == 2
    assert page1["items"][0]["type"] == "dua"  # newest first
    only_verses = client.get(URL, headers=headers, params={"type": "verse"}).json()
    assert only_verses["total"] == 5 and {i["type"] for i in only_verses["items"]} == {"verse"}


def test_users_cannot_see_or_delete_each_others_bookmarks(client, session):
    a, _ = signup_and_login(client, "a@example.com")
    b, _ = signup_and_login(client, "b@example.com")
    v = make_verse(session)
    created = client.post(URL, headers=a, json={"type": "verse", "target_id": v.id}).json()
    assert client.get(URL, headers=b).json()["total"] == 0
    assert client.delete(f"{URL}/{created['id']}", headers=b).status_code == 404
    assert client.get(URL, headers=a).json()["total"] == 1  # still there


def test_both_users_can_bookmark_the_same_verse(client, session):
    a, _ = signup_and_login(client, "a@example.com")
    b, _ = signup_and_login(client, "b@example.com")
    v = make_verse(session)
    assert client.post(URL, headers=a, json={"type": "verse", "target_id": v.id}).status_code == 201
    assert client.post(URL, headers=b, json={"type": "verse", "target_id": v.id}).status_code == 201


def test_delete_own_bookmark(client, session):
    headers, _ = signup_and_login(client)
    v = make_verse(session)
    bid = client.post(URL, headers=headers, json={"type": "verse", "target_id": v.id}).json()["id"]
    assert client.delete(f"{URL}/{bid}", headers=headers).status_code == 204
    assert client.delete(f"{URL}/{bid}", headers=headers).status_code == 404
    assert client.get(URL, headers=headers).json()["total"] == 0
