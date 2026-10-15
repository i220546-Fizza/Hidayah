from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApprovalStatus, Difficulty
from app.schemas.content import VerseOut
from app.schemas.sources import PublicSourceOut


class OptionIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class ExplanationIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    source_id: int
    reference_text: str | None = Field(None, max_length=500)


class QuestionIn(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    options: list[OptionIn] = Field(min_length=2, max_length=6)
    explanation: ExplanationIn | None = None


class QuizIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    topic: str | None = Field(None, max_length=120)
    difficulty: Difficulty
    questions: list[QuestionIn] = Field(min_length=1, max_length=50)


class PathItemIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    quiz_id: int | None = None


class PathIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    difficulty: Difficulty
    items: list[PathItemIn] = Field(min_length=1, max_length=100)


class ApprovalChange(BaseModel):
    to_status: ApprovalStatus


class OptionOut(BaseModel):
    id: int
    text: str


class QuestionOut(BaseModel):
    id: int
    prompt: str
    options: list[OptionOut]


class QuizSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    topic: str | None
    difficulty: Difficulty
    question_count: int = 0


class QuizOut(QuizSummary):
    questions: list[QuestionOut]


class AdminQuizOut(QuizSummary):
    approval_status: ApprovalStatus


class PathItemOut(BaseModel):
    position: int
    title: str
    quiz_id: int | None


class PathSummary(BaseModel):
    slug: str
    title: str
    description: str | None
    difficulty: Difficulty
    item_count: int


class PathOut(PathSummary):
    items: list[PathItemOut]
    last_item_position: int = 0
    completed: bool = False


class AdminPathOut(PathSummary):
    id: int
    approval_status: ApprovalStatus


class ProgressIn(BaseModel):
    last_item_position: int = Field(ge=0, le=1000)


class SubmitIn(BaseModel):
    answers: dict[int, int]  # question_id -> option_id


class ExplanationOut(BaseModel):
    text: str
    reference_text: str | None
    source: PublicSourceOut


class ResultOut(BaseModel):
    question_id: int
    chosen_option_id: int | None
    correct_option_id: int
    is_correct: bool
    explanation: ExplanationOut | None


class SubmitOut(BaseModel):
    attempt_id: int
    score: int
    total: int
    results: list[ResultOut]


class ReadingProgressIO(BaseModel):
    surah_number: int = Field(ge=1, le=114)
    verse_number: int = Field(ge=1)


class DailyOut(BaseModel):
    date: str
    verse: VerseOut | None
    note: str | None
