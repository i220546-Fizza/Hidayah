"""Import every model so Alembic and SQLAlchemy see the full schema."""

from app.models.email_tokens import EmailToken
from app.models.assistant import AnswerFeedback, Conversation, Message, MessageCitation
from app.models.bookmarks import Bookmark
from app.models.duas import Dua, DuaCategory
from app.models.governance import AuditEvent, EvalCase, EvalDataset, EvalResult, EvalRun
from app.models.hadith import HadithCollection, HadithGrading, HadithRecord
from app.models.learning import (
    AnswerOption,
    Explanation,
    LearningPath,
    LearningPathItem,
    Quiz,
    QuizAttempt,
    QuizAttemptAnswer,
    QuizQuestion,
    ReadingProgress,
    UserPathProgress,
)
from app.models.quran import Surah, TafsirEntry, Verse, VerseTranslation
from app.models.rag import Chunk, ChunkEmbedding, Document, IngestionJob
from app.models.sources import Source, SourceReview, SourceVersion
from app.models.users import AuthIdentity, Role, User, UserPreference, UserRole, UserSession

__all__ = [
    "AnswerFeedback", "EmailToken", "AnswerOption", "AuditEvent", "AuthIdentity", "Bookmark", "Chunk",
    "ChunkEmbedding", "Conversation", "Document", "Dua", "DuaCategory", "EvalCase",
    "EvalDataset", "EvalResult", "EvalRun", "Explanation", "HadithCollection",
    "HadithGrading", "HadithRecord", "IngestionJob", "LearningPath", "LearningPathItem",
    "Message", "MessageCitation", "Quiz", "QuizAttempt", "QuizAttemptAnswer",
    "QuizQuestion", "ReadingProgress", "Role", "Source", "SourceReview", "SourceVersion",
    "Surah", "TafsirEntry", "User", "UserPathProgress", "UserPreference", "UserRole",
    "UserSession", "Verse", "VerseTranslation",
]
