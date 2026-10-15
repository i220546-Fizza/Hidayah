"""The database itself must reject invalid data, not just the application."""
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    AnswerOption,
    Bookmark,
    Dua,
    DuaCategory,
    Message,
    MessageCitation,
    Conversation,
    Quiz,
    QuizQuestion,
    Source,
    SourceVersion,
    Surah,
    Verse,
)
from app.models.enums import (
    Difficulty,
    DuaProvenance,
    MessageRole,
    Permission,
    SourceCategory,
    SourceStatus,
    VerificationStatus,
)
from tests.factories import make_source, make_user, make_version


def _rejects(session, *objs):
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add_all(objs)


# ---------- Licensing rule ----------

def test_source_defaults_to_draft_and_unknown_rights(session):
    s = make_source(session)
    assert s.approval_status == SourceStatus.DRAFT
    assert s.commercial_use == Permission.UNKNOWN
    assert s.redistribution == Permission.UNKNOWN
    assert s.storage_permission == Permission.UNKNOWN
    assert s.indexing_permission == Permission.UNKNOWN
    assert s.rag_permission == Permission.UNKNOWN


def _approved(slug: str, **overrides) -> Source:
    """A source that satisfies EVERY approval requirement; tests then break exactly one."""
    fields = dict(
        slug=slug, title="t", category=SourceCategory.TAFSIR, language="en",
        approval_status=SourceStatus.APPROVED, verification_status=VerificationStatus.VERIFIED,
        rights_holder="x", license_name="y", license_verified_at=datetime.now(timezone.utc),
        commercial_use=Permission.ALLOWED, storage_permission=Permission.ALLOWED,
        indexing_permission=Permission.ALLOWED, rag_permission=Permission.ALLOWED,
    )
    fields.update(overrides)
    return Source(**fields)


def test_fully_documented_source_can_be_approved(session):
    s = make_source(session, approved=True)
    assert s.approval_status == SourceStatus.APPROVED


def test_helper_source_is_really_approvable(session):
    # Guards the tests below: each one must fail ONLY because of the field it breaks.
    session.add(_approved("ok-1"))
    session.flush()


@pytest.mark.parametrize("blocked", [Permission.UNKNOWN, Permission.NOT_ALLOWED, Permission.REQUIRES_PERMISSION])
def test_cannot_approve_source_when_commercial_use_not_granted(session, blocked):
    _rejects(session, _approved(f"bad-c-{blocked.value}", commercial_use=blocked))


@pytest.mark.parametrize("field", ["storage_permission", "indexing_permission", "rag_permission"])
@pytest.mark.parametrize("blocked", [Permission.UNKNOWN, Permission.NOT_ALLOWED, Permission.REQUIRES_PERMISSION])
def test_cannot_approve_source_unless_each_intended_use_is_allowed(session, field, blocked):
    _rejects(session, _approved(f"bad-{field}-{blocked.value}", **{field: blocked}))


def test_cannot_approve_source_without_licence_verification_date(session):
    _rejects(session, _approved("bad-2", license_verified_at=None))


def test_cannot_approve_source_without_rights_holder(session):
    _rejects(session, _approved("bad-3a", rights_holder=None))


def test_cannot_approve_source_without_licence_name(session):
    _rejects(session, _approved("bad-3b", license_name=None))


def test_cannot_approve_unverified_content(session):
    _rejects(session, _approved("bad-4", verification_status=VerificationStatus.UNVERIFIED))


@pytest.mark.parametrize("status", [
    SourceStatus.CANDIDATE, SourceStatus.PENDING_PERMISSION, SourceStatus.RESTRICTED,
    SourceStatus.UNDER_REVIEW, SourceStatus.REJECTED, SourceStatus.ARCHIVED,
])
def test_review_statuses_are_accepted_without_full_rights(session, status):
    """Only 'approved' needs the full licence; the review statuses record work in progress."""
    s = make_source(session, approval_status=status)
    assert s.approval_status == status
    assert s.storage_permission == Permission.UNKNOWN


def test_review_history_accepts_new_statuses(session):
    from app.models import SourceReview

    s = make_source(session)
    session.add(SourceReview(
        source_id=s.id, from_status=SourceStatus.DRAFT, to_status=SourceStatus.PENDING_PERMISSION,
        note="asked the publisher",
    ))
    session.flush()


def test_invalid_enum_value_rejected(session):
    from sqlalchemy import text

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.execute(text(
                "INSERT INTO sources (slug,title,category,language,commercial_use,redistribution,"
                "attribution_required,verification_status,approval_status) "
                "VALUES ('x','t','tafsir','en','unknown','unknown',true,'unverified','published')"))


# ---------- Versions and idempotency ----------

def test_same_file_cannot_be_registered_twice_for_a_source(session):
    s = make_source(session)
    make_version(session, s, "v1", content="same bytes")
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            make_version(session, s, "v2", content="same bytes")


def test_sources_with_versions_cannot_be_hard_deleted(session):
    s = make_source(session)
    v = make_version(session, s)
    session.add(Surah(number=1, name_arabic="x", name_english="x", verse_count=7))
    session.flush()
    session.add(Verse(surah_number=1, verse_number=1, text_arabic="x", source_version_id=v.id))
    session.flush()
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.delete(v)
            session.flush()


# ---------- Quran identifiers ----------

@pytest.mark.parametrize("number", [0, 115])
def test_surah_number_must_be_1_to_114(session, number):
    _rejects(session, Surah(number=number, name_arabic="x", name_english="x", verse_count=5))


def test_verse_unique_per_surah_verse_and_source_version(session):
    v = make_version(session, make_source(session))
    session.add(Surah(number=2, name_arabic="x", name_english="x", verse_count=286))
    session.flush()
    session.add(Verse(surah_number=2, verse_number=1, text_arabic="t", source_version_id=v.id))
    session.flush()
    _rejects(session, Verse(surah_number=2, verse_number=1, text_arabic="t2", source_version_id=v.id))


# ---------- Duas ----------

def _category(session):
    c = DuaCategory(slug=f"cat-{id(session)}", name_english="Test")
    session.add(c)
    session.flush()
    return c


def test_sourced_dua_requires_reference_and_source(session):
    c = _category(session)
    _rejects(session, Dua(category_id=c.id, title="t", arabic_text="x", provenance=DuaProvenance.SOURCED))


def test_editorial_dua_allowed_without_reference(session):
    c = _category(session)
    d = Dua(category_id=c.id, title="t", arabic_text="x", provenance=DuaProvenance.EDITORIAL)
    session.add(d)
    session.flush()
    assert d.id is not None


# ---------- Users, bookmarks, citations ----------

def test_email_must_be_lowercase(session):
    from app.models import User
    _rejects(session, User(email="Mixed@Example.test"))


def test_email_unique(session):
    make_user(session, email="a@example.com")
    from app.models import User
    _rejects(session, User(email="a@example.com"))


def _verse(session):
    v = make_version(session, make_source(session))
    if not session.get(Surah, 3):
        session.add(Surah(number=3, name_arabic="x", name_english="x", verse_count=200))
        session.flush()
    verse = Verse(surah_number=3, verse_number=1, text_arabic="t", source_version_id=v.id)
    session.add(verse)
    session.flush()
    return verse


def test_bookmark_must_have_exactly_one_target(session):
    u = make_user(session)
    _rejects(session, Bookmark(user_id=u.id))


def test_bookmark_cannot_be_duplicated(session):
    u = make_user(session)
    verse = _verse(session)
    session.add(Bookmark(user_id=u.id, verse_id=verse.id))
    session.flush()
    _rejects(session, Bookmark(user_id=u.id, verse_id=verse.id))


def test_deleting_user_removes_their_bookmarks(session):
    u = make_user(session)
    verse = _verse(session)
    session.add(Bookmark(user_id=u.id, verse_id=verse.id))
    session.flush()
    session.delete(u)
    session.flush()
    from sqlalchemy import select, func
    assert session.scalar(select(func.count()).select_from(Bookmark)) == 0


def test_citation_must_point_at_exactly_one_real_record(session):
    u = make_user(session)
    conv = Conversation(user_id=u.id)
    session.add(conv)
    session.flush()
    msg = Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="a")
    session.add(msg)
    session.flush()
    # none
    _rejects(session, MessageCitation(message_id=msg.id))
    # nonexistent target (foreign key)
    _rejects(session, MessageCitation(message_id=msg.id, verse_id=999999))
    # valid
    verse = _verse(session)
    session.add(MessageCitation(message_id=msg.id, verse_id=verse.id, is_quotation=True))
    session.flush()
    # two targets
    _rejects(session, MessageCitation(message_id=msg.id, verse_id=verse.id, chunk_id=1))


# ---------- Quiz rules ----------

def test_only_one_correct_option_per_question(session):
    quiz = Quiz(title="q", difficulty=Difficulty.BEGINNER)
    session.add(quiz)
    session.flush()
    q = QuizQuestion(quiz_id=quiz.id, position=1, prompt="p")
    session.add(q)
    session.flush()
    session.add(AnswerOption(question_id=q.id, position=1, text="a", is_correct=True))
    session.flush()
    _rejects(session, AnswerOption(question_id=q.id, position=2, text="b", is_correct=True))
    session.add(AnswerOption(question_id=q.id, position=2, text="b", is_correct=False))
    session.flush()
