"""
Ingestion pipeline tests.

All file contents here are obvious placeholders ("TEST-...") written for the tests.
They are not Quran, hadith or dua text, and they never leave the throw-away test database.
"""
import json

import pytest
from sqlalchemy import func, select

from app.core.errors import Conflict, ValidationProblem
from app.ingest.service import import_blockers, import_file
from app.models import Dua, HadithRecord, IngestionJob, SourceVersion, Surah, TafsirEntry, Verse, VerseTranslation
from app.models.enums import Permission, SourceCategory, SourceStatus
from tests.factories import make_source

SURAHS = json.dumps([
    {"number": 1, "verse_count": 3, "name_arabic": "TEST-AR-1", "name_english": "Test Surah One"},
    {"number": 2, "verse_count": 2, "name_arabic": "TEST-AR-2", "name_english": "Test Surah Two"},
]).encode()
VERSES = "# TEST header comment\n1|1|TEST-V1  with  spaces \n1|2|TEST-V2 | pipe inside é\n\n2|1|TEST-V3\r\n".encode()


def src(session, category=SourceCategory.QURAN_TEXT, **kw):
    return make_source(session, approved=True, category=category, **kw)


def do(session, source, kind, raw, label="v1", **kw):
    return import_file(session, None, source, kind=kind, raw=raw, filename="t.txt", version_label=label, **kw)


def test_gate_blocks_each_unmet_condition(session):
    s = make_source(session, category=SourceCategory.QURAN_TEXT)  # draft, rights unknown
    blockers = import_blockers(s)
    assert len(blockers) == 4
    with pytest.raises(ValidationProblem) as e:
        do(session, s, "surahs", SURAHS)
    assert e.value.errors == blockers
    assert session.scalar(select(func.count()).select_from(Surah)) == 0


@pytest.mark.parametrize("status", [SourceStatus.RESTRICTED, SourceStatus.REJECTED, SourceStatus.PENDING_PERMISSION, SourceStatus.ARCHIVED])
def test_blocked_statuses(session, status):
    s = src(session, approval_status=status)
    with pytest.raises(ValidationProblem):
        do(session, s, "surahs", SURAHS)


def test_candidate_and_under_review_may_be_imported(session):
    for status in (SourceStatus.CANDIDATE, SourceStatus.UNDER_REVIEW):
        s = src(session, approval_status=status)
        assert import_blockers(s) == []


def test_denied_commercial_use_blocks(session):
    s = src(session, approval_status=SourceStatus.CANDIDATE, commercial_use=Permission.UNKNOWN)
    with pytest.raises(ValidationProblem):
        do(session, s, "surahs", SURAHS)


def test_kind_must_match_category(session):
    s = src(session, SourceCategory.HADITH_COLLECTION)
    with pytest.raises(ValidationProblem) as e:
        do(session, s, "quran_arabic", VERSES)
    assert "does not match" in e.value.message


def test_unknown_kind(session):
    with pytest.raises(ValidationProblem):
        do(session, src(session), "nonsense", b"x")


def test_surahs_then_verses_text_kept_exactly(session):
    s = src(session)
    r = do(session, s, "surahs", SURAHS, label="surahs-1")
    assert r.counts["surahs"] == 2
    r = do(session, s, "quran_arabic", VERSES, label="text-1")
    assert r.counts == {"verses": 3}
    rows = {(v.surah_number, v.verse_number): v.text_arabic for v in session.scalars(select(Verse))}
    assert rows[(1, 1)] == "TEST-V1  with  spaces "   # inner and trailing spaces untouched
    assert rows[(1, 2)] == "TEST-V2 | pipe inside é"   # pipes after the second separator kept
    assert rows[(2, 1)] == "TEST-V3"                   # only the line ending is removed
    job = session.scalar(select(IngestionJob))
    assert job.status.value == "succeeded"


def test_same_bytes_twice_changes_nothing(session):
    s = src(session)
    do(session, s, "surahs", SURAHS)
    first = do(session, s, "quran_arabic", VERSES, label="a")
    again = do(session, s, "quran_arabic", VERSES, label="b")
    assert again.unchanged and again.version.id == first.version.id
    assert session.scalar(select(func.count()).select_from(Verse)) == 3
    assert session.scalar(select(func.count()).select_from(SourceVersion)) == 2


def test_label_reuse_with_different_content_is_a_conflict(session):
    s = src(session)
    do(session, s, "surahs", SURAHS, label="x")
    other = json.dumps([{"number": 3, "verse_count": 1, "name_arabic": "a", "name_english": "b"}]).encode()
    with pytest.raises(Conflict):
        do(session, s, "surahs", other, label="x")


def test_verses_need_surahs_first_and_write_nothing(session):
    s = src(session)
    with pytest.raises(ValidationProblem) as e:
        do(session, s, "quran_arabic", VERSES)
    assert "surah list first" in e.value.message
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Verse)) == 0


def test_one_bad_line_imports_nothing(session):
    s = src(session)
    do(session, s, "surahs", SURAHS, label="surahs")
    bad = b"1|1|TEST-A\nnot a verse line\n1|1|TEST-DUP\n1|2|\n999|1|TEST\n"
    with pytest.raises(ValidationProblem) as e:
        do(session, s, "quran_arabic", bad)
    assert len(e.value.errors) == 4
    assert session.scalar(select(func.count()).select_from(Verse)) == 0
    assert session.scalar(select(func.count()).select_from(SourceVersion)) == 1  # only the surah list


def test_bad_encoding_and_empty_file(session):
    s = src(session)
    with pytest.raises(ValidationProblem):
        do(session, s, "surahs", b"\xff\xfe\x00bad")
    do(session, s, "surahs", SURAHS, label="surahs")
    with pytest.raises(ValidationProblem):
        do(session, s, "quran_arabic", b"# only a comment\n")


def test_bom_is_removed(session):
    s = src(session)
    do(session, s, "surahs", SURAHS, label="surahs")
    do(session, s, "quran_arabic", b"\xef\xbb\xbf1|1|TEST-V1\n")
    assert session.scalar(select(Verse.text_arabic)) == "TEST-V1"


def test_translation_needs_language_and_stores_it(session):
    base = src(session)
    do(session, base, "surahs", SURAHS)
    tr = src(session, SourceCategory.QURAN_TRANSLATION, language="en")
    with pytest.raises(ValidationProblem):
        do(session, tr, "quran_translation", VERSES)
    r = do(session, tr, "quran_translation", VERSES, language="en")
    assert r.counts == {"translations": 3}
    assert {t.language for t in session.scalars(select(VerseTranslation))} == {"en"}


def test_tafsir_import_and_bad_range(session):
    do(session, src(session), "surahs", SURAHS)
    t = src(session, SourceCategory.TAFSIR, language="en")
    good = b'{"surah_number":1,"verse_start":1,"verse_end":2,"language":"en","text":"TEST tafsir"}\n'
    assert do(session, t, "tafsir", good).counts == {"tafsir_entries": 1}
    assert session.scalar(select(TafsirEntry.text)) == "TEST tafsir"
    t2 = src(session, SourceCategory.TAFSIR, language="en")
    bad = b'{"surah_number":1,"verse_start":5,"verse_end":2,"language":"en","text":"x"}\n'
    with pytest.raises(ValidationProblem):
        do(session, t2, "tafsir", bad)


def test_hadith_import_creates_collection(session):
    h = src(session, SourceCategory.HADITH_COLLECTION, language="en")
    raw = (
        '{"hadith_number":"1","translation_text":"TEST one","translation_language":"en","narrator":"TEST narrator"}\n'
        '{"hadith_number":"2a","arabic_text":"TEST-AR"}\n'
    ).encode()
    with pytest.raises(ValidationProblem):
        do(session, h, "hadith", raw)  # slug and name missing
    r = do(session, h, "hadith", raw, collection_slug="test-coll", collection_name="Test collection")
    assert r.counts == {"hadith": 2}
    assert session.scalar(select(func.count()).select_from(HadithRecord)) == 2


def test_hadith_rejects_text_less_and_duplicate_numbers(session):
    h = src(session, SourceCategory.HADITH_COLLECTION)
    raw = b'{"hadith_number":"1"}\n{"hadith_number":"2","arabic_text":"a"}\n{"hadith_number":"2","arabic_text":"b"}\n'
    with pytest.raises(ValidationProblem) as e:
        do(session, h, "hadith", raw, collection_slug="c", collection_name="C")
    assert len(e.value.errors) == 2


def test_duas_are_sourced_and_need_a_reference(session):
    d = src(session, SourceCategory.DUA)
    missing = b'{"category_slug":"c","category_name_english":"C","title":"T","arabic_text":"TEST"}\n'
    with pytest.raises(ValidationProblem):
        do(session, d, "duas", missing)
    ok = (b'{"category_slug":"c","category_name_english":"C","title":"T","arabic_text":"TEST",'
          b'"reference_text":"TEST reference"}\n')
    assert do(session, d, "duas", ok).counts == {"duas": 1}
    dua = session.scalar(select(Dua))
    assert dua.provenance.value == "sourced" and dua.reference_text == "TEST reference"


# ---- admin upload endpoint -------------------------------------------------
from tests.helpers import make_admin, signup_and_login  # noqa: E402


@pytest.fixture
def admin(client, session):
    headers, _ = signup_and_login(client, "ingest-admin@example.com")
    make_admin(session, "ingest-admin@example.com")
    return headers


def _post(client, admin, sid, raw, **params):
    return client.post(f"/api/v1/admin/sources/{sid}/imports", params=params, content=raw,
                       headers={**admin, "Content-Type": "application/octet-stream"})


def test_upload_requires_admin(client, session):
    s = src(session)
    assert _post(client, {}, s.id, SURAHS, kind="surahs", version_label="a").status_code == 401
    headers, _ = signup_and_login(client, "plain2@example.com")
    assert _post(client, headers, s.id, SURAHS, kind="surahs", version_label="a").status_code == 403


def test_upload_check_and_import(client, session, admin):
    blocked = make_source(session, category=SourceCategory.QURAN_TEXT)
    r = client.get(f"/api/v1/admin/sources/{blocked.id}/imports/check", headers=admin)
    assert r.json()["allowed"] is False and len(r.json()["blockers"]) == 4
    r = _post(client, admin, blocked.id, SURAHS, kind="surahs", version_label="a")
    assert r.status_code == 422 and len(r.json()["errors"]) == 4

    ok = src(session)
    r = _post(client, admin, ok.id, SURAHS, kind="surahs", version_label="a")
    assert r.status_code == 201 and r.json()["counts"]["surahs"] == 2
    again = _post(client, admin, ok.id, SURAHS, kind="surahs", version_label="b")
    assert again.json()["unchanged"] is True
