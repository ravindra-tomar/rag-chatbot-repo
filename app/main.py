from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
