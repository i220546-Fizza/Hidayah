"""Public content: visible only through an approved source. Data below is placeholder test data."""
import pytest

from app.models import Dua, DuaCategory, HadithCollection, HadithGrading, HadithRecord, Surah, TafsirEntry, Verse, VerseTranslation
from app.models.enums import DuaProvenance, SourceCategory, SourceStatus
from tests.factories import make_source, make_version


def _src(session, category, approved=True, **kw):
    s = make_source(session, approved=approved, category=category, **kw)
    return s, make_version(session, s, label=f"v-{s.id}", content=f"c-{s.id}")


@pytest.fixture
def world(session):
    session.add(Surah(number=1, name_arabic="TEST-AR", name_english="Test One", verse_count=2))
    session.flush()
    q_ok, q_ok_v = _src(session, SourceCategory.QURAN_TEXT, attribution_text="Credit: Test Arabic")
    q_hid, q_hid_v = _src(session, SourceCategory.QURAN_TEXT, approved=False)
    session.add_all([
        Verse(surah_number=1, verse_number=1, text_arabic="TEST-ARABIC-1", source_version_id=q_ok_v.id),
        Verse(surah_number=1, verse_number=2, text_arabic="TEST-ARABIC-2", source_version_id=q_ok_v.id),
        Verse(surah_number=1, verse_number=3, text_arabic="HIDDEN-ARABIC", source_version_id=q_hid_v.id),
    ])
    t_ok, t_ok_v = _src(session, SourceCategory.QURAN_TRANSLATION, language="en")
    t_hid, t_hid_v = _src(session, SourceCategory.QURAN_TRANSLATION, approved=False, language="en")
    session.add_all([
        VerseTranslation(surah_number=1, verse_number=1, language="en", text="TEST english uniqueword", source_version_id=t_ok_v.id),
        VerseTranslation(surah_number=1, verse_number=1, language="en", text="HIDDEN uniqueword", source_version_id=t_hid_v.id),
    ])
    k, k_v = _src(session, SourceCategory.TAFSIR, language="en")
    session.add(TafsirEntry(surah_number=1, verse_start=1, verse_end=2, language="en", text="TEST tafsir", source_version_id=k_v.id))
    h, h_v = _src(session, SourceCategory.HADITH_COLLECTION, language="en")
    hh, hh_v = _src(session, SourceCategory.HADITH_COLLECTION, approved=False, language="en")
    ok_c = HadithCollection(slug="ok-coll", name_english="OK collection", source_id=h.id)
    hid_c = HadithCollection(slug="hid-coll", name_english="Hidden collection", source_id=hh.id)
    session.add_all([ok_c, hid_c])
    session.flush()
    rec = HadithRecord(collection_id=ok_c.id, hadith_number="1", translation_text="TEST hadith uniqueword",
                       translation_language="en", source_version_id=h_v.id)
    hidden = HadithRecord(collection_id=hid_c.id, hadith_number="1", translation_text="HIDDEN hadith", translation_language="en",
                          source_version_id=hh_v.id)
    session.add_all([rec, hidden])
    session.flush()
    session.add_all([
        HadithGrading(hadith_id=rec.id, grader="Grader A", grade="TEST-grade", source_id=h.id),
        HadithGrading(hadith_id=rec.id, grader="Grader B", grade="HIDDEN-grade", source_id=hh.id),
    ])
    d, d_v = _src(session, SourceCategory.DUA)
    dh, dh_v = _src(session, SourceCategory.DUA, approved=False)
    cat = DuaCategory(slug="test-cat", name_english="Test category")
    session.add(cat)
    session.flush()
    session.add_all([
        Dua(category_id=cat.id, title="TEST dua", arabic_text="TEST-DUA-AR", provenance=DuaProvenance.SOURCED,
            reference_text="TEST ref", source_version_id=d_v.id),
        Dua(category_id=cat.id, title="HIDDEN dua", arabic_text="HIDDEN", provenance=DuaProvenance.SOURCED,
            reference_text="r", source_version_id=dh_v.id),
    ])
    session.commit()
    return {"hadith_id": rec.id, "hidden_hadith_id": hidden.id}


def test_surah_shows_only_approved_text_with_credit(client, world):
    r = client.get("/api/v1/surahs/1?language=en")
    assert r.status_code == 200
    body = r.json()
    assert [v["text_arabic"] for v in body["verses"]] == ["TEST-ARABIC-1", "TEST-ARABIC-2"]
    assert body["total"] == 2
    first = body["verses"][0]
    assert first["source"]["attribution_text"] == "Credit: Test Arabic"
    assert [t["text"] for t in first["translations"]] == ["TEST english uniqueword"]


def test_hidden_verse_and_unknown_surah(client, world):
    assert client.get("/api/v1/verses/1/3").status_code == 404
    assert client.get("/api/v1/verses/1/1").status_code == 200
    assert client.get("/api/v1/surahs/115").status_code == 422
    assert client.get("/api/v1/verses/0/1").status_code == 422


def test_approved_status_removed_hides_content(client, session, world):
    from sqlalchemy import select

    from app.models import Source
    src = session.scalar(select(Source).where(Source.category == SourceCategory.QURAN_TEXT, Source.approval_status == SourceStatus.APPROVED))
    src.approval_status = SourceStatus.UNDER_REVIEW
    session.commit()
    assert client.get("/api/v1/surahs/1").json()["verses"] == []


def test_tafsir_covers_range(client, world):
    assert [t["text"] for t in client.get("/api/v1/verses/1/2/tafsir").json()] == ["TEST tafsir"]
    assert client.get("/api/v1/verses/1/5/tafsir").json() == []


def test_hadith_only_approved_with_visible_gradings(client, world):
    cols = client.get("/api/v1/hadith/collections").json()
    assert [c["slug"] for c in cols] == ["ok-coll"] and cols[0]["record_count"] == 1
    assert client.get("/api/v1/hadith/collections/hid-coll").status_code == 404
    page = client.get("/api/v1/hadith/collections/ok-coll").json()
    assert page["total"] == 1
    one = client.get(f"/api/v1/hadith/{world['hadith_id']}").json()
    assert [g["grade"] for g in one["gradings"]] == ["TEST-grade"]
    assert client.get(f"/api/v1/hadith/{world['hidden_hadith_id']}").status_code == 404


def test_duas_only_sourced_and_approved(client, world):
    assert [c["slug"] for c in client.get("/api/v1/duas/categories").json()] == ["test-cat"]
    assert client.get("/api/v1/duas/categories").json()[0]["dua_count"] == 1
    items = client.get("/api/v1/duas?category=test-cat").json()
    assert [d["title"] for d in items] == ["TEST dua"] and items[0]["reference_text"] == "TEST ref"


def test_search_only_returns_approved_and_escapes_wildcards(client, world):
    hits = client.get("/api/v1/search?q=uniqueword").json()["hits"]
    assert {h["type"] for h in hits} == {"verse_translation", "hadith"}
    assert all("HIDDEN" not in h["snippet"] for h in hits)
    empty = client.get("/api/v1/search?q=%25%25").json()
    assert empty["hits"] == [] and "approved" in empty["note"]
    assert client.get("/api/v1/search?q=a").status_code == 422


def test_empty_database_gives_empty_lists_not_errors(client):
    assert client.get("/api/v1/surahs").json() == []
    assert client.get("/api/v1/hadith/collections").json() == []
    assert client.get("/api/v1/duas").json() == []
    assert client.get("/api/v1/search?q=anything").json()["hits"] == []
