import datetime as dt

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.learning import (
    AdminPathOut,
    AdminQuizOut,
    ApprovalChange,
    DailyOut,
    PathIn,
    PathOut,
    PathSummary,
    ProgressIn,
    QuizIn,
    QuizOut,
    QuizSummary,
    ReadingProgressIO,
    SubmitIn,
    SubmitOut,
)
from app.security.deps import get_auth_context, get_current_user, require_admin
from app.services import learning as service

router = APIRouter(tags=["learning"])
admin_router = APIRouter(prefix="/admin", tags=["admin: learning"], dependencies=[Depends(require_admin)])


from fastapi import Header  # noqa: E402

from app.core.errors import AuthError  # noqa: E402
from app.services import auth as auth_service  # noqa: E402


def maybe_user(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        user, _ = auth_service.resolve_access_token(db, authorization.split(" ", 1)[1])
    except AuthError:
        return None
    return user


@router.get("/learning/paths", response_model=list[PathSummary])
def paths(db: Session = Depends(get_db)):
    return service.approved_paths(db)


@router.get("/learning/paths/{slug}", response_model=PathOut)
def path(slug: str, user: User | None = Depends(maybe_user), db: Session = Depends(get_db)):
    return service.get_path(db, slug, user)


@router.put("/learning/paths/{slug}/progress", response_model=PathOut)
def path_progress(slug: str, payload: ProgressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.save_progress(db, user, slug, payload.last_item_position)


@router.get("/quizzes", response_model=list[QuizSummary])
def quizzes(db: Session = Depends(get_db)):
    return service.approved_quizzes(db)


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def quiz(quiz_id: int, db: Session = Depends(get_db)):
    return service.get_quiz(db, quiz_id)


@router.post("/quizzes/{quiz_id}/submit", response_model=SubmitOut)
def submit(quiz_id: int, payload: SubmitIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.submit(db, user, quiz_id, payload.answers)


@router.get("/me/reading-progress", response_model=ReadingProgressIO | None)
def get_reading(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_reading(db, user)


@router.put("/me/reading-progress", response_model=ReadingProgressIO)
def put_reading(payload: ReadingProgressIO, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.set_reading(db, user, payload.surah_number, payload.verse_number)


@router.get("/daily", response_model=DailyOut)
def daily(db: Session = Depends(get_db)):
    today = dt.datetime.now(dt.timezone.utc).date()
    verse = service.daily(db, today)
    note = None if verse else "The daily verse appears once approved Quran text is available."
    return DailyOut(date=today.isoformat(), verse=verse, note=note)


# ----- admin -----
@admin_router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return service.stats(db)


@admin_router.get("/quizzes", response_model=list[AdminQuizOut])
def admin_quizzes(db: Session = Depends(get_db)):
    return [AdminQuizOut(id=q.id, title=q.title, topic=q.topic, difficulty=q.difficulty, question_count=len(q.questions),
                         approval_status=q.approval_status) for q in service.list_quizzes_admin(db)]


@admin_router.post("/quizzes", response_model=AdminQuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(payload: QuizIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = service.create_quiz(db, actor, payload)
    return AdminQuizOut(id=q.id, title=q.title, topic=q.topic, difficulty=q.difficulty, question_count=len(q.questions), approval_status=q.approval_status)


@admin_router.post("/quizzes/{quiz_id}/status", response_model=AdminQuizOut)
def quiz_status(quiz_id: int, payload: ApprovalChange, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = service.set_quiz_status(db, actor, quiz_id, payload.to_status)
    return AdminQuizOut(id=q.id, title=q.title, topic=q.topic, difficulty=q.difficulty, question_count=len(q.questions), approval_status=q.approval_status)


@admin_router.get("/paths", response_model=list[AdminPathOut])
def admin_paths(db: Session = Depends(get_db)):
    return [AdminPathOut(id=p.id, slug=p.slug, title=p.title, description=p.description, difficulty=p.difficulty,
                         item_count=len(p.items), approval_status=p.approval_status) for p in service.list_paths_admin(db)]


@admin_router.post("/paths", response_model=AdminPathOut, status_code=status.HTTP_201_CREATED)
def create_path(payload: PathIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = service.create_path(db, actor, payload)
    return AdminPathOut(id=p.id, slug=p.slug, title=p.title, description=p.description, difficulty=p.difficulty,
                        item_count=len(p.items), approval_status=p.approval_status)


@admin_router.post("/paths/{path_id}/status", response_model=AdminPathOut)
def path_status(path_id: int, payload: ApprovalChange, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = service.set_path_status(db, actor, path_id, payload.to_status)
    return AdminPathOut(id=p.id, slug=p.slug, title=p.title, description=p.description, difficulty=p.difficulty,
                        item_count=len(p.items), approval_status=p.approval_status)
