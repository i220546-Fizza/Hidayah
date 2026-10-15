import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFound
from app.models import (
    AnswerFeedback,
    Chunk,
    Conversation,
    Dua,
    HadithCollection,
    HadithRecord,
    Message,
    MessageCitation,
    Source,
    SourceVersion,
    User,
    Verse,
    VerseTranslation,
)
from app.rag import answer as rag
from app.rag.providers import LLM, Embedder
from app.schemas.ask import AskOut, CitationOut, ConversationDetail, MessageOut
from app.schemas.sources import PublicSourceOut
from app.security.rate_limit import limiter


def _src(db: Session, version_id: int) -> PublicSourceOut:
    source = db.scalar(select(Source).join(SourceVersion, SourceVersion.source_id == Source.id).where(SourceVersion.id == version_id))
    return PublicSourceOut.model_validate(source)


def citation_out(db: Session, c: MessageCitation) -> CitationOut | None:
    """Rebuild a citation from our own records. Returns None if the record or source is gone/unapproved."""
    from app.models.enums import SourceStatus

    def ok(version_id: int) -> bool:
        s = db.scalar(select(Source).join(SourceVersion, SourceVersion.source_id == Source.id).where(SourceVersion.id == version_id))
        return s is not None and s.approval_status == SourceStatus.APPROVED

    if c.verse_id:
        v = db.get(Verse, c.verse_id)
        if v is None or not ok(v.source_version_id):
            return None
        tr = db.scalar(select(VerseTranslation).join(SourceVersion, SourceVersion.id == VerseTranslation.source_version_id)
                       .join(Source, Source.id == SourceVersion.source_id)
                       .where(VerseTranslation.surah_number == v.surah_number, VerseTranslation.verse_number == v.verse_number,
                              VerseTranslation.language == "en", Source.approval_status == SourceStatus.APPROVED))
        return CitationOut(kind="verse", label=f"Quran {v.surah_number}:{v.verse_number}", text=tr.text if tr else "",
                           text_arabic=v.text_arabic, link=f"/quran/{v.surah_number}#v{v.verse_number}", source=_src(db, v.source_version_id))
    if c.hadith_id:
        h = db.get(HadithRecord, c.hadith_id)
        if h is None or not ok(h.source_version_id):
            return None
        coll = db.get(HadithCollection, h.collection_id)
        return CitationOut(kind="hadith", label=f"{coll.name_english} #{h.hadith_number}", text=h.translation_text or "",
                           text_arabic=h.arabic_text, link=f"/hadith/{h.id}", source=_src(db, h.source_version_id))
    if c.dua_id:
        d = db.get(Dua, c.dua_id)
        if d is None or d.source_version_id is None or not ok(d.source_version_id):
            return None
        return CitationOut(kind="dua", label=f"Dua: {d.title}", text=d.translation_text or "", text_arabic=d.arabic_text,
                           link=f"/duas#{d.id}", source=_src(db, d.source_version_id))
    ch = db.get(Chunk, c.chunk_id)
    if ch is None or not ok(ch.source_version_id):
        return None
    import re
    m = re.match(r"\[(\d+:\d+(?:-\d+)?)\]\n", ch.text)
    return CitationOut(kind="chunk", label=f"Tafsir on {m.group(1)}" if m else "Tafsir passage",
                       text=ch.text[m.end():] if m else ch.text, source=_src(db, ch.source_version_id))


def message_out(db: Session, m: Message) -> MessageOut:
    cites = [x for x in (citation_out(db, c) for c in sorted(m.citations, key=lambda c: c.position)) if x]
    return MessageOut(id=m.id, role=m.role.value, content=m.content, outcome=m.outcome.value if m.outcome else None,
                      created_at=m.created_at, citations=cites)


def get_conversation(db: Session, user: User, conv_id: uuid.UUID) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if conv is None or conv.user_id != user.id:
        raise NotFound("Conversation not found.")
    return conv


def ask(db: Session, user: User, question: str, conv_id: uuid.UUID | None, llm: LLM, embedder: Embedder | None) -> AskOut:
    s = get_settings()
    limiter.check(f"ask:{user.id}", s.ask_rate_limit, s.ask_rate_window_seconds)
    if conv_id:
        conv = get_conversation(db, user, conv_id)
    else:
        conv = Conversation(user_id=user.id, title=question[:80])
        db.add(conv)
        db.flush()
    msg = rag.ask(db, user, conv, question.strip(), llm, embedder)
    db.refresh(msg)
    return AskOut(conversation_id=conv.id, message=message_out(db, msg), disclaimer=rag.DISCLAIMER)


def conversations(db: Session, user: User) -> list[Conversation]:
    return list(db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).limit(50)))


def detail(db: Session, user: User, conv_id: uuid.UUID) -> ConversationDetail:
    conv = get_conversation(db, user, conv_id)
    return ConversationDetail(id=conv.id, title=conv.title, created_at=conv.created_at,
                              messages=[message_out(db, m) for m in conv.messages])


def delete_conversation(db: Session, user: User, conv_id: uuid.UUID) -> None:
    db.delete(get_conversation(db, user, conv_id))
    db.commit()


def feedback(db: Session, user: User, message_id: int, rating: int, comment: str | None) -> None:
    msg = db.get(Message, message_id)
    if msg is None or msg.role.value != "assistant":
        raise NotFound("Message not found.")
    get_conversation(db, user, msg.conversation_id)
    row = db.scalar(select(AnswerFeedback).where(AnswerFeedback.message_id == message_id, AnswerFeedback.user_id == user.id))
    if row is None:
        row = AnswerFeedback(message_id=message_id, user_id=user.id, rating=rating, comment=comment)
        db.add(row)
    else:
        row.rating, row.comment = rating, comment
    db.commit()
