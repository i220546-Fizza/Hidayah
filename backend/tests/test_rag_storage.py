"""pgvector and full-text search must really work, not just exist."""
import hashlib

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import Chunk, ChunkEmbedding, Document
from app.models.rag import EMBEDDING_DIM
from tests.factories import make_source, make_version


def _vec(*head: float) -> list[float]:
    return list(head) + [0.0] * (EMBEDDING_DIM - len(head))


def _document(session):
    version = make_version(session, make_source(session, approved=True))
    doc = Document(
        source_version_id=version.id, original_filename="t.txt", mime_type="text/plain", byte_size=3
    )
    session.add(doc)
    session.flush()
    return doc, version


def _chunk(session, doc, version, position, body):
    c = Chunk(
        document_id=doc.id,
        source_version_id=version.id,
        position=position,
        text=body,
        checksum_sha256=hashlib.sha256(body.encode()).hexdigest(),
    )
    session.add(c)
    session.flush()
    return c


def test_nearest_neighbour_search_returns_closest_vector(session):
    doc, ver = _document(session)
    a = _chunk(session, doc, ver, 0, "alpha")
    b = _chunk(session, doc, ver, 1, "beta")
    c = _chunk(session, doc, ver, 2, "gamma")
    for chunk, v in ((a, _vec(1, 0)), (b, _vec(0, 1)), (c, _vec(0.9, 0.1))):
        session.add(ChunkEmbedding(chunk_id=chunk.id, embedding_model="test", index_version="t1", embedding=v))
    session.flush()

    nearest = session.scalars(
        select(ChunkEmbedding.chunk_id)
        .order_by(ChunkEmbedding.embedding.cosine_distance(_vec(1, 0)))
        .limit(2)
    ).all()
    assert nearest == [a.id, c.id]


def test_wrong_embedding_dimension_rejected(session):
    doc, ver = _document(session)
    ch = _chunk(session, doc, ver, 0, "alpha")
    with pytest.raises(Exception):
        with session.begin_nested():
            session.add(ChunkEmbedding(chunk_id=ch.id, embedding_model="t", index_version="1", embedding=[1.0, 2.0]))
            session.flush()


def test_full_text_search_finds_matching_chunk(session):
    doc, ver = _document(session)
    _chunk(session, doc, ver, 0, "Patience is a virtue discussed in many lessons")
    other = _chunk(session, doc, ver, 1, "Prayer times depend on the sun")
    hits = session.scalars(
        select(Chunk.id).where(Chunk.tsv.op("@@")(text("plainto_tsquery('english', 'patience')")))
    ).all()
    assert hits and other.id not in hits


def test_duplicate_chunk_text_in_document_rejected(session):
    doc, ver = _document(session)
    _chunk(session, doc, ver, 0, "same text")
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            _chunk(session, doc, ver, 1, "same text")


def test_deleting_document_removes_chunks_and_embeddings(session):
    doc, ver = _document(session)
    ch = _chunk(session, doc, ver, 0, "alpha")
    session.add(ChunkEmbedding(chunk_id=ch.id, embedding_model="t", index_version="1", embedding=_vec(1)))
    session.flush()
    session.delete(doc)
    session.flush()
    assert session.scalar(text("SELECT count(*) FROM chunks")) == 0
    assert session.scalar(text("SELECT count(*) FROM chunk_embeddings")) == 0
