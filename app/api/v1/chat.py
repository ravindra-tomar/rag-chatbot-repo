from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.rag_service import answer_with_rag
from app.api.v1.auth import get_current_user
from app.db.database import get_db
from app.db.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG chat:
    question → retrieve chunks → Gemini grounded answer + sources
    """
    try:
        result = answer_with_rag(
            payload.message,
            top_k=payload.top_k,
            session_id=payload.session_id,
            user_id=current_user.id,
            db=db,
        )
        return ChatResponse(
            session_id=result["session_id"],
            answer=result["answer"],
            used_context=result["used_context"],
            sources=[ChatSource(**src) for src in result["sources"]],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RAG chat error: {e}")
