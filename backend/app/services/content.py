"""
Read-side content. EVERY query here goes through an approved source.

A row only ever reaches a visitor if the source version it came from belongs to a source whose
status is 'approved'. Imported-but-not-approved content is invisible, by construction.
"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import (
    Dua,
    DuaCategory,
    HadithCollection,
    HadithGrading,
    HadithRecord,
    Source,
    SourceVersion,
    Surah,
    TafsirEntry,
    Verse,
    VerseTranslation,
)
from app.models.enums import SourceStatus
from app.schemas.content import (
    CollectionOut,
    DuaCategoryOut,
    DuaOut,
    GradingOut,
    HadithOut,
    SearchHit,
    SurahDetail,
    SurahOut,
    TafsirOut,
    TranslationOut,
    VerseOut,
)
from app.schemas.sources import PublicSourceOut

APPROVED = Source.approval_status == SourceStatus.APPROVED


def _credit(source: Source) -> PublicSourceOut:
    return PublicSourceOut.model_validate(source)


def list_surahs(db: Session) -> list[Surah]:
    return list(db.scalars(select(Surah).order_by(Surah.number)))


def get_surah(db: Session, number: int) -> Surah:
    surah = db.get(Surah, number)
    if surah is None:
        raise NotFound("Surah not found.")
    return surah


def _translations_for(db: Session, surah: int, verse_numbers: list[int], language: str | None):
    stmt = (
        select(VerseTranslation, Source)
        .join(SourceVersion, SourceVersion.id == VerseTranslation.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED, VerseTranslation.surah_number == surah, VerseTranslation.verse_number.in_(verse_numbers))
        .order_by(VerseTranslation.verse_number, Source.title)
    )
    if language:
        stmt = stmt.where(VerseTranslation.language == language)
    out: dict[int, list[TranslationOut]] = {}
    for tr, src in db.execute(stmt):
        out.setdefault(tr.verse_number, []).append(TranslationOut(language=tr.language, text=tr.text, source=_credit(src)))
    return out


def surah_verses(db: Session, number: int, *, language: str | None, limit: int, offset: int) -> SurahDetail:
    surah = get_surah(db, number)
    base = (
        select(Verse, Source)
        .join(SourceVersion, SourceVersion.id == Verse.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED, Verse.surah_number == number)
    )
    total = db.scalar(select(func.count(func.distinct(Verse.verse_number))).select_from(Verse)
                      .join(SourceVersion, SourceVersion.id == Verse.source_version_id)
                      .join(Source, Source.id == SourceVersion.source_id)
                      .where(APPROVED, Verse.surah_number == number)) or 0
    rows = db.execute(base.order_by(Verse.verse_number, Verse.source_version_id.desc())).all()
    seen: set[int] = set()
    chosen = []
    for verse, src in rows:  # one Arabic text per verse: the newest approved version
        if verse.verse_number not in seen:
            seen.add(verse.verse_number)
            chosen.append((verse, src))
    page = chosen[offset: offset + limit]
    trans = _translations_for(db, number, [v.verse_number for v, _ in page], language) if page else {}
    verses = [
        VerseOut(surah_number=v.surah_number, verse_number=v.verse_number, text_arabic=v.text_arabic,
                 source=_credit(s), translations=trans.get(v.verse_number, []))
        for v, s in page
    ]
    return SurahDetail(surah=SurahOut.model_validate(surah), verses=verses, total=total, limit=limit, offset=offset)


def get_verse(db: Session, surah: int, verse: int, language: str | None) -> VerseOut:
    detail = surah_verses(db, surah, language=language, limit=1000, offset=0)
    for v in detail.verses:
        if v.verse_number == verse:
            return v
    raise NotFound("That verse is not available.")


def tafsir_for(db: Session, surah: int, verse: int, language: str | None) -> list[TafsirOut]:
    stmt = (
        select(TafsirEntry, Source)
        .join(SourceVersion, SourceVersion.id == TafsirEntry.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED, TafsirEntry.surah_number == surah,
               TafsirEntry.verse_start <= verse, TafsirEntry.verse_end >= verse)
        .order_by(Source.title)
    )
    if language:
        stmt = stmt.where(TafsirEntry.language == language)
    return [
        TafsirOut(surah_number=t.surah_number, verse_start=t.verse_start, verse_end=t.verse_end,
                  language=t.language, text=t.text, source=_credit(s))
        for t, s in db.execute(stmt)
    ]


def list_collections(db: Session) -> list[CollectionOut]:
    stmt = (
        select(HadithCollection, Source, func.count(HadithRecord.id))
        .join(Source, Source.id == HadithCollection.source_id)
        .join(HadithRecord, HadithRecord.collection_id == HadithCollection.id, isouter=True)
        .where(APPROVED)
        .group_by(HadithCollection.id, Source.id)
        .order_by(HadithCollection.name_english)
    )
    return [
        CollectionOut(slug=c.slug, name_english=c.name_english, name_arabic=c.name_arabic, source=_credit(s), record_count=n)
        for c, s, n in db.execute(stmt)
    ]


def _hadith_out(db: Session, rec: HadithRecord, coll: HadithCollection, src: Source) -> HadithOut:
    gradings = db.execute(
        select(HadithGrading, Source).join(Source, Source.id == HadithGrading.source_id)
        .where(HadithGrading.hadith_id == rec.id, APPROVED).order_by(HadithGrading.grader)
    ).all()
    return HadithOut(
        id=rec.id, collection_slug=coll.slug, collection_name=coll.name_english, book_number=rec.book_number,
        book_name=rec.book_name, hadith_number=rec.hadith_number, arabic_text=rec.arabic_text,
        translation_text=rec.translation_text, translation_language=rec.translation_language,
        narrator=rec.narrator, source=_credit(src),
        gradings=[GradingOut(grader=g.grader, grade=g.grade, reference_note=g.reference_note, source=_credit(gs)) for g, gs in gradings],
    )


def _hadith_select():
    return (
        select(HadithRecord, HadithCollection, Source)
        .join(HadithCollection, HadithCollection.id == HadithRecord.collection_id)
        .join(SourceVersion, SourceVersion.id == HadithRecord.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED)
    )


def collection_records(db: Session, slug: str, *, limit: int, offset: int):
    base = _hadith_select().where(HadithCollection.slug == slug)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    if total == 0:
        raise NotFound("Collection not found.")
    rows = db.execute(base.order_by(HadithRecord.id).limit(limit).offset(offset)).all()
    return [_hadith_out(db, r, c, s) for r, c, s in rows], total


def get_hadith(db: Session, hadith_id: int) -> HadithOut:
    row = db.execute(_hadith_select().where(HadithRecord.id == hadith_id)).first()
    if row is None:
        raise NotFound("Hadith not found.")
    return _hadith_out(db, *row)


def _dua_select():
    # Sourced duas need an approved source. Editorial duas (no source) are never published
    # here: nothing is shown unless it can be traced.
    return (
        select(Dua, DuaCategory, Source)
        .join(DuaCategory, DuaCategory.id == Dua.category_id)
        .join(SourceVersion, SourceVersion.id == Dua.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED)
    )


def _dua_out(d: Dua, c: DuaCategory, s: Source) -> DuaOut:
    return DuaOut(
        id=d.id, category_slug=c.slug, title=d.title, arabic_text=d.arabic_text, transliteration=d.transliteration,
        translation_text=d.translation_text, translation_language=d.translation_language,
        provenance=d.provenance.value, reference_text=d.reference_text, source=_credit(s),
    )


def dua_categories(db: Session) -> list[DuaCategoryOut]:
    stmt = (
        select(DuaCategory, func.count(Dua.id))
        .join(Dua, Dua.category_id == DuaCategory.id)
        .join(SourceVersion, SourceVersion.id == Dua.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED)
        .group_by(DuaCategory.id)
        .order_by(DuaCategory.name_english)
    )
    return [DuaCategoryOut(slug=c.slug, name_english=c.name_english, name_urdu=c.name_urdu, dua_count=n) for c, n in db.execute(stmt)]


def duas(db: Session, category: str | None, limit: int, offset: int) -> list[DuaOut]:
    stmt = _dua_select()
    if category:
        stmt = stmt.where(DuaCategory.slug == category)
    return [_dua_out(*r) for r in db.execute(stmt.order_by(Dua.id).limit(limit).offset(offset))]


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _snippet(text: str, q: str, width: int = 160) -> str:
    i = text.lower().find(q.lower())
    if i < 0:
        return text[:width]
    start = max(0, i - width // 3)
    return ("…" if start else "") + text[start: start + width] + ("…" if start + width < len(text) else "")


def search(db: Session, q: str, limit: int = 20) -> list[SearchHit]:
    pattern = _like(q)
    hits: list[SearchHit] = []
    for tr, src in db.execute(
        select(VerseTranslation, Source).join(SourceVersion, SourceVersion.id == VerseTranslation.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(APPROVED, VerseTranslation.text.ilike(pattern, escape="\\")).limit(limit)
    ):
        hits.append(SearchHit(type="verse_translation", title=f"Quran {tr.surah_number}:{tr.verse_number}",
                              snippet=_snippet(tr.text, q), link=f"/quran/{tr.surah_number}#v{tr.verse_number}", source=_credit(src)))
    for rec, coll, src in db.execute(
        _hadith_select().where(or_(HadithRecord.translation_text.ilike(pattern, escape="\\"),
                                   HadithRecord.arabic_text.ilike(pattern, escape="\\"))).limit(limit)
    ):
        text = rec.translation_text if rec.translation_text and q.lower() in rec.translation_text.lower() else (rec.arabic_text or "")
        hits.append(SearchHit(type="hadith", title=f"{coll.name_english} #{rec.hadith_number}",
                              snippet=_snippet(text, q), link=f"/hadith/{rec.id}", source=_credit(src)))
    for d, c, src in db.execute(
        _dua_select().where(or_(Dua.title.ilike(pattern, escape="\\"), Dua.translation_text.ilike(pattern, escape="\\"),
                                Dua.arabic_text.ilike(pattern, escape="\\"))).limit(limit)
    ):
        hits.append(SearchHit(type="dua", title=d.title, snippet=_snippet(d.translation_text or d.arabic_text, q),
                              link=f"/duas#{d.id}", source=_credit(src)))
    return hits[:limit]
