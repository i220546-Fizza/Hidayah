"""
Find evidence for a question. Only approved sources whose licence allows retrieval are searched.
Keyword search (Postgres full text) always runs; vector search is added when an embedder exists.
"""
import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Chunk,
    ChunkEmbedding,
    Dua,
    HadithCollection,
    HadithRecord,
    Source,
    SourceVersion,
    Verse,
    VerseTranslation,
)
from app.models.enums import Permission, SourceStatus
from app.rag.providers import Embedder
from app.schemas.sources import PublicSourceOut

MAX_EVIDENCE = 6
MIN_RANK = 0.01

OK = (Source.approval_status == SourceStatus.APPROVED, Source.rag_permission == Permission.ALLOWED)


@dataclass
class Evidence:
    kind: str  # verse | hadith | dua | chunk
    target_id: int
    label: str  # e.g. "Quran 2:255 (translation)"
    text: str
    source: PublicSourceOut
    score: float
    link: str = ""


def _credit(s: Source) -> PublicSourceOut:
    return PublicSourceOut.model_validate(s)


def _query(q: str):
    return func.plainto_tsquery("english", q)


def retrieve(db: Session, question: str, embedder: Embedder | None = None) -> list[Evidence]:
    q = question.strip()
    found: list[Evidence] = []
    tsq = _query(q)

    tv = func.to_tsvector("english", VerseTranslation.text)
    for tr, src, rank in db.execute(
        select(VerseTranslation, Source, func.ts_rank(tv, tsq))
        .join(SourceVersion, SourceVersion.id == VerseTranslation.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(*OK, VerseTranslation.language == "en", tv.op("@@")(tsq)).order_by(func.ts_rank(tv, tsq).desc()).limit(MAX_EVIDENCE)
    ):
        # The citation points at the Arabic verse row; the English text is shown as the translation.
        verse = db.scalar(select(Verse).where(Verse.surah_number == tr.surah_number, Verse.verse_number == tr.verse_number)
                          .order_by(Verse.source_version_id.desc()))
        if verse is None:
            continue
        found.append(Evidence("verse", verse.id, f"Quran {tr.surah_number}:{tr.verse_number} (translation)", tr.text, _credit(src),
                              float(rank), f"/quran/{tr.surah_number}#v{tr.verse_number}"))

    hv = func.to_tsvector("english", func.coalesce(HadithRecord.translation_text, ""))
    for rec, coll, src, rank in db.execute(
        select(HadithRecord, HadithCollection, Source, func.ts_rank(hv, tsq))
        .join(HadithCollection, HadithCollection.id == HadithRecord.collection_id)
        .join(SourceVersion, SourceVersion.id == HadithRecord.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(*OK, hv.op("@@")(tsq)).order_by(func.ts_rank(hv, tsq).desc()).limit(MAX_EVIDENCE)
    ):
        found.append(Evidence("hadith", rec.id, f"{coll.name_english} #{rec.hadith_number}", rec.translation_text or "",
                              _credit(src), float(rank), f"/hadith/{rec.id}"))

    dv = func.to_tsvector("english", func.coalesce(Dua.title, "") + " " + func.coalesce(Dua.translation_text, ""))
    for d, src, rank in db.execute(
        select(Dua, Source, func.ts_rank(dv, tsq))
        .join(SourceVersion, SourceVersion.id == Dua.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(*OK, dv.op("@@")(tsq)).order_by(func.ts_rank(dv, tsq).desc()).limit(MAX_EVIDENCE)
    ):
        found.append(Evidence("dua", d.id, f"Dua: {d.title}", d.translation_text or d.title, _credit(src), float(rank), f"/duas#{d.id}"))

    ck_rank = func.ts_rank(Chunk.tsv, tsq)
    chunk_rows = list(db.execute(
        select(Chunk, Source, ck_rank)
        .join(SourceVersion, SourceVersion.id == Chunk.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(*OK, Source.indexing_permission == Permission.ALLOWED, Chunk.tsv.op("@@")(tsq))
        .order_by(ck_rank.desc()).limit(MAX_EVIDENCE)
    ))
    if embedder is not None:
        vec = embedder.embed([q])[0]
        dist = ChunkEmbedding.embedding.cosine_distance(vec)
        for chunk, src, d in db.execute(
            select(Chunk, Source, dist)
            .join(ChunkEmbedding, ChunkEmbedding.chunk_id == Chunk.id)
            .join(SourceVersion, SourceVersion.id == Chunk.source_version_id)
            .join(Source, Source.id == SourceVersion.source_id)
            .where(*OK, Source.indexing_permission == Permission.ALLOWED,
                   ChunkEmbedding.embedding_model == embedder.model_name, ChunkEmbedding.index_version == embedder.index_version)
            .order_by(dist).limit(MAX_EVIDENCE)
        ):
            if float(d) < 0.6:
                chunk_rows.append((chunk, src, 1.0 - float(d)))
    seen_chunks: set[int] = set()
    for chunk, src, rank in chunk_rows:
        if chunk.id in seen_chunks:
            continue
        seen_chunks.add(chunk.id)
        m = re.match(r"\[(\d+:\d+(?:-\d+)?)\]\n", chunk.text)
        label = f"Tafsir on {m.group(1)}" if m else "Tafsir passage"
        body = chunk.text[m.end():] if m else chunk.text
        found.append(Evidence("chunk", chunk.id, label, body, _credit(src), float(rank)))

    found = [e for e in found if e.score >= MIN_RANK and e.text.strip()]
    found.sort(key=lambda e: e.score, reverse=True)
    return found[:MAX_EVIDENCE]
