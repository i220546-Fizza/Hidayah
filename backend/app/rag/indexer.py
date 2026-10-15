"""Turn approved tafsir text into searchable chunks (and embeddings, when an embedder exists)."""
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, ChunkEmbedding, Document, Source, SourceVersion, TafsirEntry
from app.models.enums import Permission, SourceStatus
from app.rag.providers import Embedder

MAX_CHARS = 1500


def indexable(source: Source) -> bool:
    return (
        source.approval_status == SourceStatus.APPROVED
        and source.indexing_permission == Permission.ALLOWED
        and source.rag_permission == Permission.ALLOWED
    )


def _pieces(text: str) -> list[str]:
    out, cur = [], ""
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if cur and len(cur) + len(para) + 2 > MAX_CHARS:
            out.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out or [text.strip()]


def index_version(db: Session, version: SourceVersion, embedder: Embedder | None = None) -> int:
    """Create chunks for a tafsir version. Refuses (returns 0) unless the source is approved for it."""
    source = db.get(Source, version.source_id)
    if source is None or not indexable(source):
        return 0
    document = db.scalar(select(Document).where(Document.source_version_id == version.id))
    if document is None:
        return 0
    have = set(db.scalars(select(Chunk.checksum_sha256).where(Chunk.document_id == document.id)))
    position = len(have)
    created: list[Chunk] = []
    entries = db.scalars(select(TafsirEntry).where(TafsirEntry.source_version_id == version.id)
                         .order_by(TafsirEntry.surah_number, TafsirEntry.verse_start)).all()
    for e in entries:
        label = f"[{e.surah_number}:{e.verse_start}-{e.verse_end}]" if e.verse_end != e.verse_start else f"[{e.surah_number}:{e.verse_start}]"
        for piece in _pieces(e.text):
            text = f"{label}\n{piece}"
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest in have:
                continue
            have.add(digest)
            chunk = Chunk(document_id=document.id, source_version_id=version.id, position=position,
                          text=text, checksum_sha256=digest, token_count=len(text.split()))
            position += 1
            db.add(chunk)
            created.append(chunk)
    db.flush()
    if embedder and created:
        vectors = embedder.embed([c.text for c in created])
        for c, v in zip(created, vectors, strict=True):
            db.add(ChunkEmbedding(chunk_id=c.id, embedding_model=embedder.model_name,
                                  index_version=embedder.index_version, embedding=v))
    db.commit()
    return len(created)
