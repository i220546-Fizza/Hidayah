import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models import User
from app.rag.providers import LLM, Embedder, get_embedder, get_llm
from app.schemas.ask import AskIn, AskOut, ConversationDetail, ConversationOut, FeedbackIn
from app.security.deps import get_current_user
from app.services import ask as service

router = APIRouter(prefix="/ask", tags=["ask"])


class NotConfigured(AppError):
    status_code = 503
    default_message = "The answer assistant is not switched on yet."


def llm_dep() -> LLM:
    llm = get_llm()
    if llm is None:
        raise NotConfigured()
    return llm


def embedder_dep() -> Embedder | None:
    return get_embedder()


@router.post("", response_model=AskOut)
def ask(payload: AskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db),
        llm: LLM = Depends(llm_dep), embedder: Embedder | None = Depends(embedder_dep)):
    return service.ask(db, user, payload.question, payload.conversation_id, llm, embedder)


@router.get("/conversations", response_model=list[ConversationOut])
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.conversations(db, user)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def conversation(conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.detail(db, user, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete_conversation(db, user, conversation_id)


@router.post("/messages/{message_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def feedback(message_id: int, payload: FeedbackIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.feedback(db, user, message_id, payload.rating, payload.comment)
