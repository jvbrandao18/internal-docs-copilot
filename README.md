# Internal Docs Copilot

Internal Docs Copilot is a FastAPI backend that ingests internal documents, indexes their content, and answers questions with retrieved sources, excerpts, confidence, and audit data.

## What is it?

It is an API-first RAG backend for querying local `PDF`, `XLSX`, and `CSV` documents.

The API can:

- upload documents
- parse document content and metadata
- split content into chunks
- create embeddings
- index chunks in ChromaDB
- answer questions using retrieved evidence
- list query audit history
- reject answers when there is not enough evidence

There is no UI in this MVP. The focus is the backend pipeline, retrieval flow, source attribution, and auditability.

## Why was it built?

Internal documentation is often spread across PDFs, spreadsheets, and CSV exports. Finding an answer can require manual reading, business context, and trust in responses that may not clearly show their source.

This project was built to demonstrate a simple and inspectable RAG backend. It avoids hiding the retrieval process behind a large orchestration framework and keeps the main responsibilities visible: parsing, chunking, embeddings, vector search, answer generation, source attribution, refusal behavior, persistence, and tests.

## How does it work?

A client uploads a document to `/documents/upload`. The service stores the file locally, extracts text and metadata, creates chunks, persists document records in SQLite, and indexes embeddings in ChromaDB.

When a client sends a question to `/queries/ask`, the service embeds the question, retrieves relevant chunks, builds an answer from the recovered evidence, stores query/audit data, and returns:

- `answer`
- `confidence`
- `sources`
- `retrieved_chunks`
- `latency_ms`

If the retrieved evidence is insufficient, the application returns a controlled refusal instead of guessing.

### Main technologies

- Python 3.12
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- SQLite
- PyMuPDF
- pandas
- openpyxl
- ChromaDB
- OpenAI API
- Pytest
- Ruff
- Black
- Docker Compose

### API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/documents/upload` | Upload and ingest a document |
| `GET` | `/documents` | List ingested documents |
| `GET` | `/documents/{document_id}` | Retrieve document details |
| `DELETE` | `/documents/{document_id}` | Delete a document |
| `POST` | `/queries/ask` | Ask a question using retrieved document context |
| `GET` | `/audit/queries` | List query audit sessions |
| `GET` | `/audit/queries/{query_id}` | Retrieve the audit trail for one query |
| `GET` | `/docs` | Swagger API documentation |

### Example usage

Health check:

```bash
curl http://localhost:8000/health
```

Upload a document:

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@docs/policies.csv"
```

Ask a question:

```bash
curl -X POST http://localhost:8000/queries/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the password policy?",
    "document_ids": [],
    "top_k": 5
  }'
```

### Project structure

```text
app/
  main.py                 FastAPI application factory
  api/                    Routes and dependencies
  core/                   Configuration, exceptions, and logging
  database/               SQLAlchemy base, session, and models
  infra/llm/              OpenAI chat and embedding clients
  infra/parsers/          PDF, XLSX, and CSV parsers
  infra/vectorstore/      ChromaDB integration
  repositories/           SQLite repositories
  schemas/                Pydantic request and response schemas
  services/               Ingestion, chunking, retrieval, answer, and audit logic
tests/
  integration/
  unit/
Dockerfile
docker-compose.yml
pyproject.toml
```

## How do I run it?

### Configure environment

Create a `.env` file from `.env.example` and set `OPENAI_API_KEY` before running document upload and question answering against real embeddings and chat completion.

Important variables:

- `APP_NAME`
- `APP_ENV`
- `APP_DEBUG`
- `SQLITE_URL`
- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `CHROMA_PERSIST_DIR`
- `UPLOAD_DIR`
- `LOG_LEVEL`
- `PDF_CHUNK_SIZE`
- `PDF_CHUNK_OVERLAP`
- `DEFAULT_TOP_K`
- `MIN_EVIDENCE_SCORE`

### Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn app.main:app --reload
```

Open:

- Swagger docs: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

### Tests and validation

```bash
python -m pytest
python -m ruff check .
python -m black --check .
```
