# FastAPI RAG Chatbot (Gemini + Chroma)

This project is a basic end-to-end RAG chatbot backend built with FastAPI.

It supports:
- Document upload (`.txt` / `.pdf`)
- Text extraction and chunking
- Embeddings with Gemini
- Vector storage and retrieval with Chroma
- RAG-based chat with source citations
- Basic in-memory chat session memory

## Tech Stack

- FastAPI
- Uvicorn
- Google Gemini (`google-genai`)
- ChromaDB
- PyPDF
- Pydantic

## Project Flow

1. Upload document
2. Extract text
3. Split into chunks
4. Create embeddings
5. Store vectors in Chroma
6. Ask questions in chat
7. Retrieve relevant chunks and generate grounded answer

## Setup

```powershell
cd "C:\Users\i tech\OneDrive\Desktop\test-fast-api"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" pydantic-settings python-multipart python-dotenv
pip install google-genai chromadb pypdf
```

## Environment Variables (`.env`)

```env
APP_NAME=RAG Chatbot
GEMINI_API_KEY=your_gemini_key
CHAT_MODEL=gemini-3.6-flash
UPLOAD_DIR=./data/uploads
CHUNK_SIZE=800
CHUNK_OVERLAP=150
CHROMA_PATH=./data/chroma
CHROMA_COLLECTION=documents
EMBEDDING_MODEL=gemini-embedding-001
TOP_K=4
```

## Run Server

Preferred:

```powershell
.\start_server.ps1
```

Direct:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```

Swagger docs:
- http://127.0.0.1:8000/docs

## API Endpoints

### Health
- `GET /health`

### Documents
- `POST /api/v1/documents/upload` (form-data: `file`)
- `GET /api/v1/documents`
- `DELETE /api/v1/documents/{doc_id}`
- `POST /api/v1/documents/search`

Example search body:

```json
{
  "query": "casual leave kitne hain?",
  "top_k": 3
}
```

### Chat (RAG + memory)
- `POST /api/v1/chat`

Example request:

```json
{
  "message": "WFH kitne din allowed hain?",
  "top_k": 3,
  "session_id": null
}
```

Notes:
- First call can send `session_id: null`
- Response returns a `session_id`
- Reuse same `session_id` in next calls for chat continuity

## Data Storage

- Uploaded files and metadata: `data/uploads/`
- Vector DB files: `data/chroma/`

## Current Limitations

- Memory is in-process only (resets on server restart)
- No authentication yet
- No relational DB for users/messages yet

## Suggested Next Steps

- Persist chat memory in DB (Postgres/SQLite)
- Add JWT auth and user-wise document isolation
- Add async background jobs for large file ingestion
- Add evaluation script for retrieval quality
