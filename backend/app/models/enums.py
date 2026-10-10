import enum

from sqlalchemy import Enum


def pg_enum(py_enum: type[enum.Enum], name: str) -> Enum:
    """Store enums as VARCHAR + CHECK constraint (easy to migrate, still validated)."""
    return Enum(
        py_enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda e: [m.value for m in e],
        length=40,
    )


class SourceCategory(str, enum.Enum):
    QURAN_TEXT = "quran_text"
    QURAN_TRANSLATION = "quran_translation"
    TAFSIR = "tafsir"
    HADITH_COLLECTION = "hadith_collection"
    HADITH_GRADING = "hadith_grading"
    DUA = "dua"
    EDUCATIONAL = "educational"


class ApprovalStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class Permission(str, enum.Enum):
    """Used for commercial use and redistribution. UNKNOWN is the safe default."""

    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"
    REQUIRES_PERMISSION = "requires_permission"
    UNKNOWN = "unknown"


class IngestionStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DuaProvenance(str, enum.Enum):
    SOURCED = "sourced"
    EDITORIAL = "editorial"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class AnswerOutcome(str, enum.Enum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ERROR = "error"


class Difficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EvalCaseKind(str, enum.Enum):
    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE = "multi_source"
    AMBIGUOUS = "ambiguous"
    DIFFERING_VIEWS = "differing_views"
    NO_EVIDENCE = "no_evidence"
