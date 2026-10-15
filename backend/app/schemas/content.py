from pydantic import BaseModel, ConfigDict

from app.schemas.sources import PublicSourceOut


class Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SurahOut(Orm):
    number: int
    name_arabic: str
    name_english: str
    name_transliterated: str | None
    verse_count: int


class TranslationOut(BaseModel):
    language: str
    text: str
    source: PublicSourceOut


class VerseOut(BaseModel):
    surah_number: int
    verse_number: int
    text_arabic: str
    source: PublicSourceOut
    translations: list[TranslationOut] = []


class SurahDetail(BaseModel):
    surah: SurahOut
    verses: list[VerseOut]
    total: int
    limit: int
    offset: int


class TafsirOut(BaseModel):
    surah_number: int
    verse_start: int
    verse_end: int
    language: str
    text: str
    source: PublicSourceOut


class CollectionOut(BaseModel):
    slug: str
    name_english: str
    name_arabic: str | None
    source: PublicSourceOut
    record_count: int


class GradingOut(BaseModel):
    grader: str
    grade: str
    reference_note: str | None
    source: PublicSourceOut


class HadithOut(BaseModel):
    id: int
    collection_slug: str
    collection_name: str
    book_number: str | None
    book_name: str | None
    hadith_number: str
    arabic_text: str | None
    translation_text: str | None
    translation_language: str | None
    narrator: str | None
    source: PublicSourceOut
    gradings: list[GradingOut] = []


class DuaCategoryOut(Orm):
    slug: str
    name_english: str
    name_urdu: str | None
    dua_count: int = 0


class DuaOut(BaseModel):
    id: int
    category_slug: str
    title: str
    arabic_text: str
    transliteration: str | None
    translation_text: str | None
    translation_language: str | None
    provenance: str
    reference_text: str | None
    source: PublicSourceOut | None


class SearchHit(BaseModel):
    type: str  # verse_translation | hadith | dua | tafsir
    title: str
    snippet: str
    link: str
    source: PublicSourceOut


class SearchResults(BaseModel):
    query: str
    hits: list[SearchHit]
    note: str | None = None
