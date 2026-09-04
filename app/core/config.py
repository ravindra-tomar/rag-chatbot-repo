from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "RAG Chatbot"
    GEMINI_API_KEY: str = ""
    CHAT_MODEL: str = "gemini-3.6-flash"
    DATABASE_URL: str = "sqlite:///./data/app.db"
    POSTGRES_PASSWORD: str = ""
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_UPLOAD_SIZE_MB: int = 10

    # Phase 3: documents
    UPLOAD_DIR: str = "./data/uploads"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Phase 4: embeddings + vector DB
    CHROMA_PATH: str = "./data/chroma"
    CHROMA_COLLECTION: str = "documents"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    TOP_K: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
