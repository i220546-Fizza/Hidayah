import datetime as dt
import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound, ValidationProblem
from app.models import (
    AnswerOption,
    Explanation,
    LearningPath,
    LearningPathItem,
    Quiz,
    QuizAttempt,
    QuizAttemptAnswer,
    QuizQuestion,
    ReadingProgress,
    Source,
    Surah,
    User,
    UserPathProgress,
)
from app.models.enums import ApprovalStatus, SourceStatus
from app.schemas.learning import (
    ExplanationOut,
    PathIn,
    PathItemOut,
    PathOut,
    PathSummary,
    QuestionOut,
    OptionOut,
    QuizIn,
    QuizOut,
    QuizSummary,
    ResultOut,
    SubmitOut,
)
from app.schemas.sources import PublicSourceOut
from app.services import audit
from app.services import content


# ---------- learner side ----------
def approved_paths(db: Session) -> list[PathSummary]:
    rows = db.scalars(select(LearningPath).where(LearningPath.approval_status == ApprovalStatus.APPROVED).order_by(LearningPath.title))
    return [PathSummary(slug=p.slug, title=p.title, description=p.description, difficulty=p.difficulty, item_count=len(p.items)) for p in rows]


def get_path(db: Session, slug: str, user: User | None) -> PathOut:
    p = db.scalar(select(LearningPath).where(LearningPath.slug == slug, LearningPath.approval_status == ApprovalStatus.APPROVED))
    if p is None:
        raise NotFound("Learning path not found.")
    prog = db.get(UserPathProgress, (user.id, p.id)) if user else None
    return PathOut(
        slug=p.slug, title=p.title, description=p.description, difficulty=p.difficulty, item_count=len(p.items),
        items=[PathItemOut(position=i.position, title=i.title, quiz_id=i.quiz_id) for i in p.items],
        last_item_position=prog.last_item_position if prog else 0,
        completed=bool(prog and prog.completed_at),
    )


def save_progress(db: Session, user: User, slug: str, position: int) -> PathOut:
    p = db.scalar(select(LearningPath).where(LearningPath.slug == slug, LearningPath.approval_status == ApprovalStatus.APPROVED))
    if p is None:
        raise NotFound("Learning path not found.")
    if position > len(p.items):
        raise ValidationProblem("That step does not exist in this path.")
    prog = db.get(UserPathProgress, (user.id, p.id)) or UserPathProgress(user_id=user.id, path_id=p.id, last_item_position=0)
    db.add(prog)
    prog.last_item_position = max(prog.last_item_position, position)
    if prog.last_item_position >= len(p.items) and prog.completed_at is None:
        prog.completed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return get_path(db, slug, user)


def approved_quizzes(db: Session) -> list[QuizSummary]:
    rows = db.scalars(select(Quiz).where(Quiz.approval_status == ApprovalStatus.APPROVED).order_by(Quiz.title))
    return [QuizSummary(id=q.id, title=q.title, topic=q.topic, difficulty=q.difficulty, question_count=len(q.questions)) for q in rows]


def _approved_quiz(db: Session, quiz_id: int) -> Quiz:
    q = db.get(Quiz, quiz_id)
    if q is None or q.approval_status != ApprovalStatus.APPROVED:
        raise NotFound("Quiz not found.")
    return q


def get_quiz(db: Session, quiz_id: int) -> QuizOut:
    q = _approved_quiz(db, quiz_id)
    return QuizOut(  # correct answers are never sent before submitting
        id=q.id, title=q.title, topic=q.topic, difficulty=q.difficulty, question_count=len(q.questions),
        questions=[QuestionOut(id=x.id, prompt=x.prompt, options=[OptionOut(id=o.id, text=o.text) for o in x.options]) for x in q.questions],
    )


def submit(db: Session, user: User, quiz_id: int, answers: dict[int, int]) -> SubmitOut:
    q = _approved_quiz(db, quiz_id)
    valid_questions = {x.id for x in q.questions}
    if set(answers) - valid_questions:
        raise ValidationProblem("Some answers do not belong to this quiz.")
    attempt = QuizAttempt(user_id=user.id, quiz_id=q.id, completed_at=dt.datetime.now(dt.timezone.utc))
    db.add(attempt)
    db.flush()
    results, score = [], 0
    for x in q.questions:
        correct = next(o for o in x.options if o.is_correct)
        chosen = answers.get(x.id)
        if chosen is not None and chosen not in {o.id for o in x.options}:
            raise ValidationProblem("An answer option does not belong to its question.")
        ok = chosen == correct.id
        score += ok
        if chosen is not None:
            db.add(QuizAttemptAnswer(attempt_id=attempt.id, question_id=x.id, option_id=chosen, is_correct=ok))
        exp = None
        if x.explanation and x.explanation.source_id:
            src = db.get(Source, x.explanation.source_id)
            if src and src.approval_status == SourceStatus.APPROVED:  # hide explanations whose source lost approval
                exp = ExplanationOut(text=x.explanation.text, reference_text=x.explanation.reference_text, source=PublicSourceOut.model_validate(src))
        results.append(ResultOut(question_id=x.id, chosen_option_id=chosen, correct_option_id=correct.id, is_correct=ok, explanation=exp))
    attempt.score = score
    db.commit()
    return SubmitOut(attempt_id=attempt.id, score=score, total=len(q.questions), results=results)


def get_reading(db: Session, user: User) -> ReadingProgress | None:
    return db.get(ReadingProgress, user.id)


def set_reading(db: Session, user: User, surah: int, verse: int) -> ReadingProgress:
    s = db.get(Surah, surah)
    if s is None or verse > s.verse_count:
        raise ValidationProblem("That place is not in the Quran text we hold.")
    row = db.get(ReadingProgress, user.id) or ReadingProgress(user_id=user.id, surah_number=surah, verse_number=verse)
    row.surah_number, row.verse_number = surah, verse
    db.add(row)
    db.commit()
    return row


def daily(db: Session, today: dt.date):
    """A verse picked by date from verses we may show. Same verse all day, nothing invented."""
    from app.models import SourceVersion, Verse

    base = (
        select(Verse.surah_number, Verse.verse_number)
        .join(SourceVersion, SourceVersion.id == Verse.source_version_id)
        .join(Source, Source.id == SourceVersion.source_id)
        .where(content.APPROVED)
        .distinct()
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    if total == 0:
        return None
    pick = int(hashlib.sha256(today.isoformat().encode()).hexdigest(), 16) % total
    surah_no, verse_no = db.execute(base.order_by(Verse.surah_number, Verse.verse_number).offset(pick).limit(1)).one()
    return content.get_verse(db, surah_no, verse_no, "en")


# ---------- admin authoring ----------
def create_quiz(db: Session, actor: User, data: QuizIn) -> Quiz:
    quiz = Quiz(title=data.title, topic=data.topic, difficulty=data.difficulty)
    for pos, qd in enumerate(data.questions, start=1):
        if sum(o.is_correct for o in qd.options) != 1:
            raise ValidationProblem(f"Question {pos} must have exactly one correct option.")
        question = QuizQuestion(position=pos, prompt=qd.prompt)
        question.options = [AnswerOption(position=i, text=o.text, is_correct=o.is_correct) for i, o in enumerate(qd.options, start=1)]
        if qd.explanation:
            if db.get(Source, qd.explanation.source_id) is None:
                raise ValidationProblem(f"Question {pos}: explanation source not found.")
            question.explanation = Explanation(**qd.explanation.model_dump())
        quiz.questions.append(question)
    db.add(quiz)
    db.flush()
    audit.record(db, actor.id, "quiz_created", "quiz", quiz.id, {"title": quiz.title})
    db.commit()
    return quiz


def quiz_blockers(db: Session, quiz: Quiz) -> list[str]:
    out = []
    for x in quiz.questions:
        e = x.explanation
        src = db.get(Source, e.source_id) if e and e.source_id else None
        if src is None or src.approval_status != SourceStatus.APPROVED:
            out.append(f"Question {x.position} needs an explanation backed by an approved source.")
    return out


def set_quiz_status(db: Session, actor: User, quiz_id: int, to: ApprovalStatus) -> Quiz:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise NotFound("Quiz not found.")
    if to == ApprovalStatus.APPROVED:
        problems = quiz_blockers(db, quiz)
        if problems:
            raise ValidationProblem("This quiz cannot be approved yet.", errors=problems)
    quiz.approval_status = to
    audit.record(db, actor.id, "quiz_status_changed", "quiz", quiz.id, {"to": to.value})
    db.commit()
    return quiz


def list_quizzes_admin(db: Session) -> list[Quiz]:
    return list(db.scalars(select(Quiz).order_by(Quiz.id.desc())))


def create_path(db: Session, actor: User, data: PathIn) -> LearningPath:
    if db.scalar(select(LearningPath).where(LearningPath.slug == data.slug)):
        raise Conflict("A path with that slug already exists.")
    for it in data.items:
        if it.quiz_id and db.get(Quiz, it.quiz_id) is None:
            raise ValidationProblem("A step refers to a quiz that does not exist.")
    path = LearningPath(slug=data.slug, title=data.title, description=data.description, difficulty=data.difficulty)
    path.items = [LearningPathItem(position=i, title=it.title, quiz_id=it.quiz_id) for i, it in enumerate(data.items, start=1)]
    db.add(path)
    db.flush()
    audit.record(db, actor.id, "path_created", "learning_path", path.id, {"slug": path.slug})
    db.commit()
    return path


def set_path_status(db: Session, actor: User, path_id: int, to: ApprovalStatus) -> LearningPath:
    path = db.get(LearningPath, path_id)
    if path is None:
        raise NotFound("Path not found.")
    if to == ApprovalStatus.APPROVED:
        bad = [i.title for i in path.items if i.quiz_id and db.get(Quiz, i.quiz_id).approval_status != ApprovalStatus.APPROVED]
        if bad:
            raise ValidationProblem("This path cannot be approved yet.", errors=[f"Quiz for '{t}' is not approved." for t in bad])
    path.approval_status = to
    audit.record(db, actor.id, "path_status_changed", "learning_path", path.id, {"to": to.value})
    db.commit()
    return path


def list_paths_admin(db: Session) -> list[LearningPath]:
    return list(db.scalars(select(LearningPath).order_by(LearningPath.id.desc())))


def stats(db: Session) -> dict:
    from app.models import AnswerFeedback, Conversation, Message, Source as S, SourceVersion
    from app.models.enums import AnswerOutcome

    def n(model, *where):
        return db.scalar(select(func.count()).select_from(model).where(*where)) or 0

    by_status = {s: 0 for s in SourceStatus}
    for st, c in db.execute(select(S.approval_status, func.count()).group_by(S.approval_status)):
        by_status[st] = c
    outcomes = {o.value: n(Message, Message.outcome == o) for o in AnswerOutcome}
    return {
        "users": n(User),
        "sources_by_status": {k.value: v for k, v in by_status.items()},
        "source_versions": n(SourceVersion),
        "conversations": n(Conversation),
        "answer_outcomes": outcomes,
        "feedback_up": n(AnswerFeedback, AnswerFeedback.rating == 1),
        "feedback_down": n(AnswerFeedback, AnswerFeedback.rating == -1),
        "quizzes_approved": n(Quiz, Quiz.approval_status == ApprovalStatus.APPROVED),
        "paths_approved": n(LearningPath, LearningPath.approval_status == ApprovalStatus.APPROVED),
    }
