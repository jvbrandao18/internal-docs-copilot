# internal-docs-copilot

API backend para consulta auditavel de documentos corporativos com RAG.

## Objetivo do projeto

O `internal-docs-copilot` foi criado para responder perguntas sobre documentos internos da empresa de forma rastreavel e segura.

Em vez de responder com base em memoria ou suposicoes, o sistema:

1. recebe documentos em `PDF`, `XLSX` e `CSV`;
2. extrai e organiza o conteudo com metadados;
3. quebra o texto em partes menores;
4. gera embeddings e indexa os vetores;
5. responde perguntas somente com base no contexto recuperado;
6. devolve citacoes, trechos de apoio e trilha de auditoria.

O foco do MVP e permitir uma base tecnica confiavel para busca semantica e respostas fundamentadas em documentos internos.

## O que o projeto faz

- Upload de documentos corporativos em `PDF`, `XLSX` e `CSV`
- Parsing com metadados por pagina, planilha e linha
- Chunking configuravel para indexacao semantica
- Geracao de embeddings com OpenAI
- Armazenamento vetorial com ChromaDB
- Persistencia de metadados e auditoria em SQLite
- Endpoint de perguntas com resposta baseada em evidencias
- Retorno de citacoes, trechos e confianca
- Recusa segura quando nao ha evidencia suficiente
- Logging estruturado em JSON

## Escopo do MVP

### Dentro do MVP

- API-only
- Upload e remocao de documentos
- Listagem de documentos indexados
- Perguntas sobre a base indexada
- Auditoria de ingestao e consultas

### Fora do MVP

- Interface web
- Autenticacao
- OCR
- Multiusuario
- Reranker

## Como funciona

### 1. Ingestao

O usuario envia um arquivo para a API. O backend salva o documento, identifica o parser correto e extrai o conteudo util.

### 2. Estruturacao

O conteudo extraido e enriquecido com metadados de origem, como pagina do PDF, nome da planilha ou numero da linha.

### 3. Chunking

O texto e dividido em blocos menores com overlap configuravel para melhorar a recuperacao semantica.

### 4. Embeddings e indexacao

Cada chunk recebe um embedding pela OpenAI e e armazenado no ChromaDB. Os metadados e eventos de auditoria ficam no SQLite.

### 5. Consulta

Quando uma pergunta chega, o sistema busca os chunks mais relevantes, monta o contexto e solicita uma resposta fundamentada.

### 6. Resposta segura

Se a evidencia recuperada for fraca ou insuficiente, a API recusa a resposta em vez de inventar informacao.

## Arquitetura

- `app/api`: rotas HTTP e injecao de dependencias
- `app/core`: configuracao, logging, excecoes e container da aplicacao
- `app/db`: modelos SQLAlchemy, sessao e repositorios
- `app/domain/services`: casos de uso do MVP
- `app/infra/parsers`: extracao de PDF, XLSX e CSV
- `app/infra/openai`: cliente de embeddings e resposta
- `app/infra/vector`: integracao com ChromaDB
- `app/schemas`: contratos Pydantic da API

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

## Endpoints principais

- `GET /api/v1/health`
  Verifica o estado da API, banco e store vetorial.
- `POST /api/v1/documents/upload`
  Faz upload, parsing e indexacao de um documento.
- `GET /api/v1/documents`
  Lista documentos processados.
- `DELETE /api/v1/documents/{document_id}`
  Remove documento e vetores associados.
- `POST /api/v1/queries/ask`
  Responde perguntas com base no contexto recuperado.
- `GET /api/v1/audit/events`
  Lista eventos de auditoria.

## Exemplo de fluxo

1. Suba um arquivo de politica interna para `/api/v1/documents/upload`.
2. O backend extrai o conteudo e indexa os chunks.
3. Envie uma pergunta para `/api/v1/queries/ask`.
4. Receba uma resposta com:
   - texto final;
   - score de confianca;
   - citacoes;
   - trechos usados como evidencia;
   - indicacao de recusa quando faltar base documental.

## Como rodar localmente

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .[dev]
copy .env.example .env
uvicorn app.main:app --reload
```

Depois, acesse:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Variaveis de ambiente

O arquivo `.env.example` traz a configuracao inicial. As variaveis mais importantes sao:

- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL`
- `OPENAI_CHAT_MODEL`
- `SQLITE_DB_PATH`
- `CHROMA_PATH`
- `UPLOADS_DIR`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K_RESULTS`
- `MIN_EVIDENCE_SCORE`

## Desenvolvimento

### Testes

```bash
pytest
```

### Qualidade de codigo

```bash
ruff check .
black --check .
```

## Docker

```bash
copy .env.example .env
docker compose up --build
```

## Estado atual

Este repositorio ja contem o bootstrap funcional do backend com:

- estrutura de aplicacao organizada;
- endpoints principais do MVP;
- integracao com SQLite, ChromaDB e OpenAI;
- testes unitarios para parsers e chunking;
- configuracao de lint, formatacao e containerizacao.
