"""
Answer assistant tests. The model here is a scripted STAND-IN (FakeLLM), not Claude:
these tests prove our guard rails, not the quality of real answers. Content is placeholder text.
"""
import json

import pytest
from sqlalchemy import func, select

from app.api.v1.ask import embedder_dep, llm_dep
from app.models import Chunk, Document, Dua, DuaCategory, HadithCollection, HadithRecord, MessageCitation, Surah, TafsirEntry, Verse, VerseTranslation
from app.models.enums import DuaProvenance, SourceCategory
from app.rag.indexer import index_version
from app.rag.providers import LLMError
from tests.factories import make_source, make_version
from tests.helpers import signup_and_login


class FakeLLM:
    def __init__(self, reply="", error=False):
        self.reply, self.error, self.calls = reply, error, []

    def complete(self, system, user, max_tokens=900):
        self.calls.append((system, user))
        if self.error:
            raise LLMError("down")
        return self.reply


class FakeEmbedder:
    model_name, index_version = "fake-test", "t1"

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * 1024
            v[0 if "alpha" in t.lower() else 1] = 1.0
            out.append(v)
        return out


def _s(session, category, approved=True, **kw):
    s = make_source(session, approved=approved, category=category, **kw)
    return s, make_version(session, s, label=f"v{s.id}", content=f"c{s.id}")


@pytest.fixture
def data(session):
    session.add(Surah(number=1, name_arabic="TEST", name_english="T", verse_count=3))
    session.flush()
    q, qv = _s(session, SourceCategory.QURAN_TEXT)
    t, tv = _s(session, SourceCategory.QURAN_TRANSLATION, language="en")
    th, thv = _s(session, SourceCategory.QURAN_TRANSLATION, approved=False, language="en")
    session.add(Verse(surah_number=1, verse_number=1, text_arabic="TEST-AR-TEXT", source_version_id=qv.id))
    session.add(VerseTranslation(surah_number=1, verse_number=1, language="en", text="Patience is a virtue for believers",
                                 source_version_id=tv.id))
    session.add(VerseTranslation(surah_number=1, verse_number=1, language="en", text="Zebra hidden content",
                                 source_version_id=thv.id))
    h, hv = _s(session, SourceCategory.HADITH_COLLECTION, language="en")
    c = HadithCollection(slug="c", name_english="Test coll", source_id=h.id)
    session.add(c)
    session.flush()
    session.add(HadithRecord(collection_id=c.id, hadith_number="7", translation_text="Kindness brings reward",
                             translation_language="en", source_version_id=hv.id))
    session.commit()
    return {}


@pytest.fixture
def auth(client):
    headers, _ = signup_and_login(client, "asker@example.com")
    return headers


def use(client, llm, embedder=None):
    client.app.dependency_overrides[llm_dep] = lambda: llm
    client.app.dependency_overrides[embedder_dep] = lambda: embedder
    return llm


def ask(client, auth, q="What about patience?", **extra):
    return client.post("/api/v1/ask", json={"question": q, **extra}, headers=auth)


def test_requires_login(client):
    assert client.post("/api/v1/ask", json={"question": "hello there"}).status_code == 401


def test_not_configured_is_an_honest_503(client, auth, data):
    # no key in the test environment and no override
    r = ask(client, auth)
    assert r.status_code == 503 and "not switched on" in r.json()["detail"]


def test_no_evidence_means_no_model_call(client, auth, data):
    llm = use(client, FakeLLM('{"answer":"made up [E1]","used":[1]}'))
    r = ask(client, auth, "quantum spaceships")
    body = r.json()
    assert r.status_code == 200 and body["message"]["outcome"] == "insufficient_evidence"
    assert body["message"]["citations"] == [] and llm.calls == []


def test_answer_with_citations_from_our_records(client, auth, data):
    llm = use(client, FakeLLM('{"answer":"Patience is praised [E1].","used":[1]}'))
    body = ask(client, auth).json()
    m = body["message"]
    assert m["outcome"] == "answered" and "[E1]" in m["content"]
    cite = m["citations"][0]
    assert cite["kind"] == "verse" and cite["text_arabic"] == "TEST-AR-TEXT" and cite["text"] == "Patience is a virtue for believers"
    assert "not a fatwa" in body["disclaimer"]
    system, user = llm.calls[0]
    assert "Zebra" not in user  # unapproved translation never reaches the model
    assert "Patience is a virtue" in user


def test_unknown_evidence_number_is_discarded(client, auth, data):
    use(client, FakeLLM('{"answer":"x [E9]","used":[9]}'))
    m = ask(client, auth).json()["message"]
    assert m["outcome"] == "error" and m["citations"] == []


def test_arabic_in_model_output_is_rejected(client, auth, data):
    use(client, FakeLLM('{"answer":"هذا [E1]","used":[1]}'))
    assert ask(client, auth).json()["message"]["outcome"] == "error"


@pytest.mark.parametrize("reply", ["not json at all", '{"answer":"no citations","used":[]}', '{"answer":"","used":[1]}'])
def test_malformed_model_output_is_an_error(client, auth, data, reply):
    use(client, FakeLLM(reply))
    assert ask(client, auth).json()["message"]["outcome"] == "error"


def test_provider_failure_is_an_error_not_a_crash(client, auth, data):
    use(client, FakeLLM(error=True))
    r = ask(client, auth)
    assert r.status_code == 200 and r.json()["message"]["outcome"] == "error"


def test_conversation_history_owner_only_and_feedback(client, auth, data, session):
    use(client, FakeLLM('{"answer":"Kindness [E1].","used":[1]}'))
    body = ask(client, auth, "kindness reward?").json()
    cid, mid = body["conversation_id"], body["message"]["id"]
    assert body["message"]["citations"][0]["kind"] == "hadith"
    detail = client.get(f"/api/v1/ask/conversations/{cid}", headers=auth).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert client.post(f"/api/v1/ask/messages/{mid}/feedback", json={"rating": 1}, headers=auth).status_code == 204
    assert client.post(f"/api/v1/ask/messages/{mid}/feedback", json={"rating": 5}, headers=auth).status_code == 422
    other, _ = signup_and_login(client, "other@example.com")
    assert client.get(f"/api/v1/ask/conversations/{cid}", headers=other).status_code == 404
    assert client.post(f"/api/v1/ask/messages/{mid}/feedback", json={"rating": 1}, headers=other).status_code == 404
    follow = ask(client, auth, "patience again?", conversation_id=cid).json()
    assert follow["conversation_id"] == cid
    assert client.delete(f"/api/v1/ask/conversations/{cid}", headers=auth).status_code == 204
    assert session.scalar(select(func.count()).select_from(MessageCitation)) == 0


def test_citation_disappears_if_source_is_no_longer_approved(client, auth, data, session):
    use(client, FakeLLM('{"answer":"Kindness [E1].","used":[1]}'))
    cid = ask(client, auth, "kindness reward?").json()["conversation_id"]
    from app.models import Source
    from app.models.enums import SourceStatus
    for s in session.scalars(select(Source)):
        s.approval_status = SourceStatus.UNDER_REVIEW
    session.commit()
    detail = client.get(f"/api/v1/ask/conversations/{cid}", headers=auth).json()
    assert detail["messages"][1]["citations"] == []


def test_question_length_limits(client, auth, data):
    use(client, FakeLLM("{}"))
    assert ask(client, auth, "ab").status_code == 422
    assert ask(client, auth, "x" * 1001).status_code == 422


def test_rate_limit(client, auth, data, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "ask_rate_limit", 2)
    use(client, FakeLLM('{"answer":"Kindness [E1].","used":[1]}'))
    assert [ask(client, auth, "kindness reward?").status_code for _ in range(3)] == [200, 200, 429]


def test_tafsir_chunks_and_vector_retrieval(client, auth, data, session):
    k, kv = _s(session, SourceCategory.TAFSIR, language="en")
    doc = Document(source_version_id=kv.id, original_filename="t.json", mime_type="application/json", byte_size=1)
    session.add(doc)
    session.add(TafsirEntry(surah_number=1, verse_start=1, verse_end=2, language="en",
                            text="Alpha commentary paragraph one.\n\nSecond paragraph.", source_version_id=kv.id))
    session.commit()
    assert index_version(session, kv, FakeEmbedder()) == 1
    assert index_version(session, kv, FakeEmbedder()) == 0  # idempotent
    llm = use(client, FakeLLM('{"answer":"See [E1].","used":[1]}'), FakeEmbedder())
    m = ask(client, auth, "alpha").json()["message"]  # no keyword overlap needed beyond the vector hit
    assert m["citations"][0]["kind"] == "chunk" and m["citations"][0]["label"] == "Tafsir on 1:1-2"
    assert "[1:1-2]" not in m["citations"][0]["text"]


def test_unapproved_source_is_never_indexed(session, data):
    k, kv = _s(session, SourceCategory.TAFSIR, approved=False, language="en")
    session.add(Document(source_version_id=kv.id, original_filename="t", mime_type="x", byte_size=1))
    session.add(TafsirEntry(surah_number=1, verse_start=1, verse_end=1, language="en", text="x", source_version_id=kv.id))
    session.commit()
    assert index_version(session, kv, None) == 0
    assert session.scalar(select(func.count()).select_from(Chunk)) == 0
