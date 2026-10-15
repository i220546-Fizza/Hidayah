"""
Import a file as a new version of a registered source.

Rules enforced here (and again by the database where possible):
  * the source's licence is verified and commercial use + permanent storage are 'allowed';
  * the source status is candidate, under_review or approved (never draft/pending/restricted/rejected);
  * the file kind matches the source category;
  * the whole file is validated first; nothing is written unless every line is valid;
  * the file is identified by SHA-256, so importing the same bytes twice changes nothing.

Imported rows are NOT public until the source itself is 'approved'; every content API checks that.
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, ValidationProblem
from app.ingest import parsers
from app.models import (
    Document,
    Dua,
    DuaCategory,
    HadithCollection,
    HadithRecord,
    IngestionJob,
    Source,
    SourceVersion,
    Surah,
    TafsirEntry,
    User,
    Verse,
    VerseTranslation,
)
from app.models.enums import (
    DuaProvenance,
    IngestionStatus,
    Permission,
    SourceCategory,
    SourceStatus,
)
from app.services import audit

KINDS = {
    "surahs": SourceCategory.QURAN_TEXT,
    "quran_arabic": SourceCategory.QURAN_TEXT,
    "quran_translation": SourceCategory.QURAN_TRANSLATION,
    "tafsir": SourceCategory.TAFSIR,
    "hadith": SourceCategory.HADITH_COLLECTION,
    "duas": SourceCategory.DUA,
}
ALLOWED_STATUSES = {SourceStatus.CANDIDATE, SourceStatus.UNDER_REVIEW, SourceStatus.APPROVED}
BLOCKED_REASON = {
    SourceStatus.DRAFT: "it is still a draft",
    SourceStatus.PENDING_PERMISSION: "we are still waiting for permission",
    SourceStatus.RESTRICTED: "its terms conflict with our use",
    SourceStatus.REJECTED: "it was rejected",
    SourceStatus.ARCHIVED: "it is archived",
}


@dataclass
class ImportResult:
    version: SourceVersion
    unchanged: bool
    counts: dict[str, int]


def import_blockers(source: Source) -> list[str]:
    problems: list[str] = []
    if source.approval_status not in ALLOWED_STATUSES:
        problems.append(f"The source cannot be imported while {BLOCKED_REASON.get(source.approval_status, 'its status blocks it')}.")
    if source.license_verified_at is None:
        problems.append("The licence has not been verified by a person.")
    if source.commercial_use != Permission.ALLOWED:
        problems.append(f"Commercial use is '{source.commercial_use.value}', not 'allowed'.")
    if source.storage_permission != Permission.ALLOWED:
        problems.append(f"Permanent storage is '{source.storage_permission.value}', not 'allowed'.")
    return problems


def _parse(kind: str, text: str) -> parsers.Parsed:
    if kind in ("quran_arabic", "quran_translation"):
        return parsers.parse_verse_lines(text)
    return {
        "surahs": parsers.parse_surahs, "tafsir": parsers.parse_tafsir,
        "hadith": parsers.parse_hadith, "duas": parsers.parse_duas,
    }[kind](text)


def import_file(
    db: Session,
    actor: User | None,
    source: Source,
    *,
    kind: str,
    raw: bytes,
    filename: str,
    version_label: str,
    language: str | None = None,
    collection_slug: str | None = None,
    collection_name: str | None = None,
) -> ImportResult:
    if kind not in KINDS:
        raise ValidationProblem(f"Unknown file kind '{kind}'.", errors=[f"Use one of: {', '.join(sorted(KINDS))}."])
    if source.category != KINDS[kind]:
        raise ValidationProblem(
            "That file kind does not match the source.",
            errors=[f"'{kind}' belongs to category '{KINDS[kind].value}', but this source is '{source.category.value}'."],
        )
    blockers = import_blockers(source)
    if blockers:
        raise ValidationProblem("This source may not be imported yet.", errors=blockers)
    if kind == "quran_translation" and not language:
        raise ValidationProblem("A language code is required for this kind of file.")
    if kind == "hadith" and not (collection_slug and collection_name):
        raise ValidationProblem("A collection slug and name are required for hadith files.")

    checksum = hashlib.sha256(raw).hexdigest()
    existing = db.scalar(
        select(SourceVersion).where(SourceVersion.source_id == source.id, SourceVersion.checksum_sha256 == checksum)
    )
    if existing is not None:
        return ImportResult(existing, True, {})
    if db.scalar(select(SourceVersion).where(SourceVersion.source_id == source.id, SourceVersion.version_label == version_label)):
        raise Conflict("That version label is already used by different content.")

    try:
        text = parsers.decode(raw)
    except ValueError as exc:
        raise ValidationProblem(str(exc)) from None
    parsed = _parse(kind, text)
    if parsed.errors:
        raise ValidationProblem("The file has problems; nothing was imported.", errors=parsed.errors)

    # --- all valid: write everything in one transaction ---
    version = SourceVersion(
        source_id=source.id, version_label=version_label, checksum_sha256=checksum,
        notes=f"kind={kind}; file={filename}",
    )
    db.add(version)
    db.flush()
    document = Document(
        source_version_id=version.id, original_filename=filename[:300],
        mime_type="text/plain" if kind in ("quran_arabic", "quran_translation") else "application/json",
        byte_size=len(raw),
    )
    db.add(document)
    db.flush()
    job = IngestionJob(
        document_id=document.id, status=IngestionStatus.RUNNING, attempts=1,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    counts = _write(db, kind, parsed.records, source, version, language, collection_slug, collection_name)
    job.status = IngestionStatus.SUCCEEDED
    job.finished_at = datetime.now(timezone.utc)
    audit.record(
        db, actor.id if actor else None, "source_version_imported", "source", source.id,
        {"version": version_label, "kind": kind, "sha256": checksum, **counts},
    )
    db.commit()
    return ImportResult(version, False, counts)


def _write(db, kind, records, source, version, language, collection_slug, collection_name) -> dict[str, int]:
    if kind == "surahs":
        have = set(db.scalars(select(Surah.number)))
        new = [r for r in records if r["number"] not in have]
        if new:
            db.execute(insert(Surah), new)
        return {"surahs": len(new), "skipped_existing": len(records) - len(new)}

    if kind in ("quran_arabic", "quran_translation", "tafsir"):
        needed = {r["surah_number"] for r in records}
        known = set(db.scalars(select(Surah.number).where(Surah.number.in_(needed))))
        absent = sorted(needed - known)
        if absent:
            raise ValidationProblem(
                "Import the surah list first.",
                errors=[f"Surah numbers not yet registered: {', '.join(map(str, absent[:20]))}."],
            )

    if kind == "quran_arabic":
        db.execute(insert(Verse), [
            {"surah_number": r["surah_number"], "verse_number": r["verse_number"], "text_arabic": r["text"],
             "source_version_id": version.id} for r in records])
        return {"verses": len(records)}
    if kind == "quran_translation":
        db.execute(insert(VerseTranslation), [
            {"surah_number": r["surah_number"], "verse_number": r["verse_number"], "language": language,
             "text": r["text"], "source_version_id": version.id} for r in records])
        return {"translations": len(records)}
    if kind == "tafsir":
        db.execute(insert(TafsirEntry), [
            {"surah_number": r["surah_number"], "verse_start": r["verse_start"], "verse_end": r["verse_end"],
             "language": r["language"], "text": r["text"], "source_version_id": version.id} for r in records])
        return {"tafsir_entries": len(records)}
    if kind == "hadith":
        collection = db.scalar(select(HadithCollection).where(HadithCollection.slug == collection_slug))
        if collection is None:
            collection = HadithCollection(slug=collection_slug, name_english=collection_name, source_id=source.id)
            db.add(collection)
            db.flush()
        elif collection.source_id != source.id:
            raise Conflict("That collection belongs to a different source.")
        db.execute(insert(HadithRecord), [
            {**{k: r.get(k) for k in parsers.HADITH_REQUIRED + parsers.HADITH_OPTIONAL},
             "collection_id": collection.id, "source_version_id": version.id} for r in records])
        return {"hadith": len(records)}
    # duas
    cats: dict[str, int] = {}
    for r in records:
        slug = r["category_slug"]
        if slug not in cats:
            cat = db.scalar(select(DuaCategory).where(DuaCategory.slug == slug))
            if cat is None:
                cat = DuaCategory(slug=slug, name_english=r["category_name_english"])
                db.add(cat)
                db.flush()
            cats[slug] = cat.id
    db.execute(insert(Dua), [
        {"category_id": cats[r["category_slug"]], "title": r["title"], "arabic_text": r["arabic_text"],
         "transliteration": r.get("transliteration"), "translation_text": r.get("translation_text"),
         "translation_language": r.get("translation_language"), "provenance": DuaProvenance.SOURCED.value,
         "reference_text": r["reference_text"], "source_version_id": version.id} for r in records])
    return {"duas": len(records)}
