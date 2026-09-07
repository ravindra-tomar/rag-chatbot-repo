# FastAPI RAG Chatbot (Gemini + Chroma)

This project is a basic end-to-end RAG chatbot backend built with FastAPI.

It supports:
- Document upload (`.txt` / `.pdf`)
- Text extraction and chunking
- Embeddings with Gemini
- Vector storage and retrieval with Chroma
- RAG-based chat with source citations
- Persistent chat session memory in SQLite

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
pip install pytest httpx sqlalchemy "python-jose[cryptography]" email-validator
pip install "psycopg[binary]" alembic
alembic upgrade head
```

## Environment Variables (`.env`)

```env
APP_NAME=RAG Chatbot
GEMINI_API_KEY=your_gemini_key
CHAT_MODEL=gemini-3.6-flash
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
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

After changing database models, create and apply an Alembic migration:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Swagger docs:
- http://127.0.0.1:8000/docs

## API Endpoints

### Health
- `GET /health`

### Documents
- `POST /api/v1/documents/upload` (Bearer token + form-data: `file`)
- `POST /api/v1/documents/upload-multiple` (Bearer token + repeated form-data: `files`)
- `GET /api/v1/documents` (Bearer token)
- `DELETE /api/v1/documents/{doc_id}` (Bearer token)
- `POST /api/v1/documents/search` (Bearer token)

Uploads are deduplicated per user using a SHA-256 content hash. Re-uploading the
same content returns `status: duplicate` without creating new vectors. Uploading
changed content with the same filename re-indexes the new file and removes the
previous version. New files are appended to the existing knowledge base.

### Frontend

The React/Vite frontend is in `frontend/` and includes authentication, chat,
multi-file upload, document management, duplicate/update status, and source
citations.

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The frontend expects the API at
`http://127.0.0.1:8000`; set `VITE_API_URL` if the backend runs elsewhere.

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

Register/login body:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Use the returned `access_token` as `Authorization: Bearer <token>` for chat and document APIs.

Example search body:

```json
{
  "query": "casual leave kitne hain?",
  "top_k": 3
}
```

### Chat (RAG + memory)
- `POST /api/v1/chat` (Bearer token)

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

- Chat memory is persisted in SQLite during development
- SQLite persistence is currently intended for development; use PostgreSQL for production
- Existing documents ingested before authentication are not assigned to a user
- Docker Compose setup uses PostgreSQL for the API database and named volumes for uploads/vector data

## Suggested Next Steps

- Add async background jobs for large file ingestion
- Add evaluation script for retrieval quality

## Docker Deployment

Set `GEMINI_API_KEY`, `SECRET_KEY`, and `POSTGRES_PASSWORD` in your local environment, then run:

```powershell
docker compose up --build
```

The API will be available at `http://localhost:8000/docs`.

For Railway, deploy this repository as a Docker service, add a PostgreSQL service,
then set `DATABASE_URL` to Railway's PostgreSQL connection string. Add the required
variables in Railway Variables. Railway provides `PORT` automatically.

## Railway + Vercel Deployment

1. Deploy the repository from GitHub to Railway. Railway uses the root `Dockerfile`.
2. Add a Railway PostgreSQL service and reference its `DATABASE_URL` from the API service.
3. Add `GEMINI_API_KEY`, `SECRET_KEY`, `FRONTEND_URL`, and the runtime values listed below.
4. Generate a Railway public domain and verify `/health` and `/docs`.
5. Add a Railway volume mounted at `/app/data` so uploads and Chroma vectors persist.
6. Import the same repository into Vercel and set the root directory to `frontend`.
7. Set the Vercel build command to `npm run build` and output directory to `dist`.
8. Set Vercel variable `VITE_API_URL` to the Railway API URL, then redeploy.
9. Set Railway variable `FRONTEND_URL` to the Vercel URL, then redeploy the API.

Railway API variables to add in the service dashboard:

```text
APP_NAME=RAG Chatbot
CHAT_MODEL=gemini-3.6-flash
ACCESS_TOKEN_EXPIRE_MINUTES=60
MAX_UPLOAD_SIZE_MB=10
FRONTEND_URL=https://your-frontend.vercel.app
UPLOAD_DIR=/app/data/uploads
CHROMA_PATH=/app/data/chroma
CHROMA_COLLECTION=documents
EMBEDDING_MODEL=gemini-embedding-001
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K=4
```

Add `DATABASE_URL` using the PostgreSQL service reference. Add
`GEMINI_API_KEY` and `SECRET_KEY` as secret variables. Do not add `PORT`; Railway
provides it automatically.

The Docker image runs `alembic upgrade head` before starting Uvicorn. Never commit
`.env`, API keys, database passwords, `frontend/node_modules`, or `frontend/dist`.
