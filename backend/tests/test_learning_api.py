"""Learning paths, quizzes, progress, daily verse and admin stats. Placeholder content only."""
import pytest

from app.models import Surah, Verse
from app.models.enums import SourceCategory
from tests.factories import make_source, make_version
from tests.helpers import make_admin, signup_and_login


@pytest.fixture
def admin(client, session):
    headers, _ = signup_and_login(client, "ladmin@example.com")
    make_admin(session, "ladmin@example.com")
    return headers


@pytest.fixture
def user(client):
    return signup_and_login(client, "learner@example.com")[0]


def quiz_payload(source_id, **over):
    q = {"title": "Test quiz", "topic": "test", "difficulty": "beginner", "questions": [
        {"prompt": "Test question one?", "options": [{"text": "wrong"}, {"text": "right", "is_correct": True}],
         "explanation": {"text": "Because the test says so", "source_id": source_id, "reference_text": "TEST ref"}},
        {"prompt": "Test question two?", "options": [{"text": "yes", "is_correct": True}, {"text": "no"}],
         "explanation": {"text": "Reason two", "source_id": source_id}},
    ]}
    q.update(over)
    return q


def approved_quiz(client, admin, session):
    src = make_source(session, approved=True, category=SourceCategory.EDUCATIONAL)
    session.commit()
    r = client.post("/api/v1/admin/quizzes", json=quiz_payload(src.id), headers=admin)
    assert r.status_code == 201, r.text
    qid = r.json()["id"]
    assert client.post(f"/api/v1/admin/quizzes/{qid}/status", json={"to_status": "approved"}, headers=admin).status_code == 200
    return qid, src


def test_authoring_requires_admin(client, user):
    assert client.post("/api/v1/admin/quizzes", json={}, headers=user).status_code == 403
    assert client.get("/api/v1/admin/stats", headers=user).status_code == 403


def test_quiz_needs_exactly_one_correct_option(client, admin, session):
    src = make_source(session, approved=True, category=SourceCategory.EDUCATIONAL)
    session.commit()
    bad = quiz_payload(src.id)
    bad["questions"][0]["options"] = [{"text": "a"}, {"text": "b"}]
    assert client.post("/api/v1/admin/quizzes", json=bad, headers=admin).status_code == 422


def test_quiz_cannot_be_approved_without_approved_source(client, admin, session):
    src = make_source(session, category=SourceCategory.EDUCATIONAL)  # draft source
    session.commit()
    qid = client.post("/api/v1/admin/quizzes", json=quiz_payload(src.id), headers=admin).json()["id"]
    r = client.post(f"/api/v1/admin/quizzes/{qid}/status", json={"to_status": "approved"}, headers=admin)
    assert r.status_code == 422 and len(r.json()["errors"]) == 2
    assert client.get("/api/v1/quizzes").json() == []
    assert client.get(f"/api/v1/quizzes/{qid}").status_code == 404


def test_learner_never_sees_correct_flag_and_gets_scored(client, admin, user, session):
    qid, _ = approved_quiz(client, admin, session)
    quiz = client.get(f"/api/v1/quizzes/{qid}").json()
    assert "is_correct" not in str(quiz) and quiz["question_count"] == 2
    q1, q2 = quiz["questions"]
    from app.models import AnswerOption
    from sqlalchemy import select
    correct = {o.question_id: o.id for o in session.scalars(select(AnswerOption).where(AnswerOption.is_correct))}
    wrong_q1 = next(o["id"] for o in q1["options"] if o["id"] != correct[q1["id"]])
    r = client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {q1["id"]: wrong_q1, q2["id"]: correct[q2["id"]]}}, headers=user)
    body = r.json()
    assert r.status_code == 200 and body["score"] == 1 and body["total"] == 2
    assert [x["is_correct"] for x in body["results"]] == [False, True]
    assert body["results"][0]["correct_option_id"] == correct[q1["id"]]
    assert body["results"][0]["explanation"]["source"]["slug"]


def test_submit_rejects_foreign_ids_and_anonymous(client, admin, user, session):
    qid, _ = approved_quiz(client, admin, session)
    assert client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {}}).status_code == 401
    assert client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {"999999": 1}}, headers=user).status_code == 422
    quiz = client.get(f"/api/v1/quizzes/{qid}").json()
    q1 = quiz["questions"][0]["id"]
    assert client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {str(q1): 999999}}, headers=user).status_code == 422


def test_unanswered_questions_count_as_wrong(client, admin, user, session):
    qid, _ = approved_quiz(client, admin, session)
    assert client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {}}, headers=user).json()["score"] == 0


def test_explanation_hidden_when_source_loses_approval(client, admin, user, session):
    from app.models.enums import SourceStatus
    qid, src = approved_quiz(client, admin, session)
    src.approval_status = SourceStatus.UNDER_REVIEW
    session.commit()
    r = client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": {}}, headers=user).json()
    assert all(x["explanation"] is None for x in r["results"])


def test_paths_progress_and_completion(client, admin, user, session):
    qid, _ = approved_quiz(client, admin, session)
    payload = {"slug": "test-path", "title": "Test path", "difficulty": "beginner",
               "items": [{"title": "Step one"}, {"title": "Step two", "quiz_id": qid}]}
    pid = client.post("/api/v1/admin/paths", json=payload, headers=admin).json()["id"]
    assert client.post("/api/v1/admin/paths", json=payload, headers=admin).status_code == 409
    assert client.get("/api/v1/learning/paths").json() == []
    assert client.post(f"/api/v1/admin/paths/{pid}/status", json={"to_status": "approved"}, headers=admin).status_code == 200
    assert [p["slug"] for p in client.get("/api/v1/learning/paths").json()] == ["test-path"]
    assert client.put("/api/v1/learning/paths/test-path/progress", json={"last_item_position": 1}).status_code == 401
    r = client.put("/api/v1/learning/paths/test-path/progress", json={"last_item_position": 1}, headers=user).json()
    assert r["last_item_position"] == 1 and r["completed"] is False
    assert client.put("/api/v1/learning/paths/test-path/progress", json={"last_item_position": 3}, headers=user).status_code == 422
    assert client.put("/api/v1/learning/paths/test-path/progress", json={"last_item_position": 2}, headers=user).json()["completed"] is True
    assert client.get("/api/v1/learning/paths/test-path", headers=user).json()["completed"] is True
    assert client.get("/api/v1/learning/paths/test-path").json()["completed"] is False  # anonymous: no progress


def test_path_with_unapproved_quiz_cannot_be_approved(client, admin, session):
    src = make_source(session, approved=True, category=SourceCategory.EDUCATIONAL)
    session.commit()
    qid = client.post("/api/v1/admin/quizzes", json=quiz_payload(src.id), headers=admin).json()["id"]
    pid = client.post("/api/v1/admin/paths", json={"slug": "p2", "title": "Path two", "difficulty": "beginner",
                                                    "items": [{"title": "Step", "quiz_id": qid}]}, headers=admin).json()["id"]
    assert client.post(f"/api/v1/admin/paths/{pid}/status", json={"to_status": "approved"}, headers=admin).status_code == 422


def test_reading_progress(client, user, session):
    session.add(Surah(number=1, name_arabic="T", name_english="T", verse_count=7))
    session.commit()
    assert client.get("/api/v1/me/reading-progress", headers=user).json() is None
    assert client.put("/api/v1/me/reading-progress", json={"surah_number": 1, "verse_number": 8}, headers=user).status_code == 422
    assert client.put("/api/v1/me/reading-progress", json={"surah_number": 1, "verse_number": 3}, headers=user).status_code == 200
    assert client.get("/api/v1/me/reading-progress", headers=user).json() == {"surah_number": 1, "verse_number": 3}


def test_daily_is_empty_then_stable(client, session):
    r = client.get("/api/v1/daily").json()
    assert r["verse"] is None and "approved" in r["note"]
    session.add(Surah(number=1, name_arabic="T", name_english="T", verse_count=5))
    session.flush()
    src = make_source(session, approved=True, category=SourceCategory.QURAN_TEXT)
    v = make_version(session, src)
    session.add_all([Verse(surah_number=1, verse_number=i, text_arabic=f"TEST-{i}", source_version_id=v.id) for i in range(1, 6)])
    session.commit()
    a, b = client.get("/api/v1/daily").json(), client.get("/api/v1/daily").json()
    assert a["verse"]["text_arabic"].startswith("TEST-") and a == b


def test_admin_stats(client, admin):
    s = client.get("/api/v1/admin/stats", headers=admin).json()
    assert s["users"] >= 1 and s["sources_by_status"]["draft"] == 0 and "answered" in s["answer_outcomes"]
