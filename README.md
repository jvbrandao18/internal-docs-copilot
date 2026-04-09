# internal-docs-copilot
Corporate document copilot with RAG for auditable question answering over PDFs and spreadsheets.

## MVP
API que recebe PDF/XLSX/CSV, indexa conteudo e responde perguntas com citacoes, trechos e trilha de auditoria.

## Stack
- Python 3.12
- FastAPI + Uvicorn
- Pydantic v2
- PyMuPDF
- pandas + openpyxl
- ChromaDB
- SQLite + SQLAlchemy
- OpenAI API
- pytest
- Ruff + Black
- Docker

## Features
- Upload de PDF, XLSX e CSV
- Parsing com metadados por pagina, planilha e linha
- Chunking com overlap configuravel
- Embeddings com OpenAI
- Indexacao vetorial em ChromaDB
- Metadados e trilha de auditoria em SQLite
- Endpoint de pergunta com resposta fundamentada em contexto recuperado
- Citacoes, trechos, score de evidencia e recusa segura quando nao ha base suficiente
- Logging estruturado em JSON

## Arquitetura
- `app/api`: rotas e dependencias HTTP
- `app/core`: configuracao, logging, excecoes e container de aplicacao
- `app/db`: modelos SQLAlchemy, sessao e repositorios
- `app/domain/services`: casos de uso do MVP
- `app/infra`: parsers, OpenAI e ChromaDB
- `app/schemas`: contratos HTTP com Pydantic

## Endpoints
- `GET /api/v1/health`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `DELETE /api/v1/documents/{document_id}`
- `POST /api/v1/queries/ask`
- `GET /api/v1/audit/events`

## Setup local
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .[dev]
copy .env.example .env
uvicorn app.main:app --reload
```

## Variaveis de ambiente
Veja `.env.example`. As principais sao:
- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL`
- `OPENAI_CHAT_MODEL`
- `SQLITE_DB_PATH`
- `CHROMA_PATH`
- `UPLOADS_DIR`

## Fluxo do MVP
1. Envie um documento para `/documents/upload`.
2. O backend salva o arquivo, extrai o conteudo, gera chunks e embeddings.
3. Os vetores vao para o ChromaDB e os metadados para SQLite.
4. Consulte `/queries/ask` para obter resposta, citacoes e confianca.
5. Inspecione `/audit/events` para a trilha de auditoria.

## Testes e qualidade
```bash
pytest
ruff check .
black --check .
```

## Docker
```bash
copy .env.example .env
docker compose up --build
```
