import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.sources import PublicSourceOut


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    conversation_id: uuid.UUID | None = None


class CitationOut(BaseModel):
    kind: str
    label: str
    text: str  # exact text from our records, never written by the model
    text_arabic: str | None = None
    link: str | None = None
    source: PublicSourceOut


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    outcome: str | None
    created_at: datetime
    citations: list[CitationOut] = []


class AskOut(BaseModel):
    conversation_id: uuid.UUID
    message: MessageOut
    disclaimer: str


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class FeedbackIn(BaseModel):
    rating: int = Field(ge=-1, le=1)
    comment: str | None = Field(None, max_length=1000)
