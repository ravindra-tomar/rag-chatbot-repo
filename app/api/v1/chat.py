from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.rag_service import answer_with_rag

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """
    RAG chat:
    question → retrieve chunks → Gemini grounded answer + sources
    """
    try:
        result = answer_with_rag(
            payload.message,
            top_k=payload.top_k,
            session_id=payload.session_id,
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
