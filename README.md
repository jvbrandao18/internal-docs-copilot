# internal-docs-copilot

Backend API-first para consulta auditável de documentos corporativos com RAG sobre arquivos `PDF`, `XLSX` e `CSV`.

## Visão geral

Este projeto demonstra como construir um copilot interno simples, explícito e confiável para responder perguntas sobre documentos empresariais. A proposta não é criar um chatbot genérico: a API só deve responder quando houver evidência recuperada da base indexada.

O fluxo do MVP é direto:

1. receber um arquivo;
2. extrair conteúdo e metadados;
3. gerar chunks;
4. criar embeddings;
5. indexar vetores no ChromaDB;
6. recuperar contexto relevante para uma pergunta;
7. responder com fontes, trechos, confiança e trilha de auditoria.

Quando a evidência é insuficiente, a aplicação recusa a resposta de forma previsível e segura.

## Problema

Documentação interna costuma ficar espalhada entre PDFs, planilhas e exports CSV. Encontrar respostas rápidas exige leitura manual, contexto de negócio e, muitas vezes, confiança em respostas que não deixam claro de onde vieram.

## Solução

O `internal-docs-copilot` organiza esse fluxo em uma API backend enxuta:

- upload de documentos `PDF`, `XLSX` e `CSV`;
- parsing com preservação de metadados de origem;
- chunking apropriado para texto corrido e planilhas;
- indexação vetorial com ChromaDB;
- persistência relacional de documentos, chunks e auditoria em SQLite;
- respostas baseadas apenas em contexto recuperado;
- recusa segura quando não houver base documental suficiente.

## O que o projeto faz

- expõe endpoints HTTP para ingestão, consulta e auditoria;
- salva os arquivos enviados localmente em `data/uploads`;
- registra metadados e histórico de consultas em SQLite;
- indexa embeddings em `data/chroma`;
- retorna resposta, confiança, fontes, trechos, quantidade de chunks recuperados e latência;
- mantém logging estruturado em JSON para facilitar observabilidade local e futura evolução.

## Escopo do MVP

Dentro do MVP:

- API sem interface gráfica;
- upload, listagem, inspeção e remoção de documentos;
- suporte a `PDF`, `XLSX` e `CSV`;
- endpoint de perguntas com contexto recuperado;
- auditoria de consultas;
- recusa segura sem evidência.

Fora do MVP:

- autenticação;
- UI;
- OCR;
- multiusuário;
- reranker;
- workers assíncronos.

## Arquitetura

O projeto segue uma estrutura em camadas, com responsabilidade explícita por pasta:

- `app/api`: rotas FastAPI e dependências;
- `app/core`: configuração, exceções e logging estruturado;
- `app/database`: base SQLAlchemy, sessão e modelos ORM;
- `app/repositories`: acesso ao SQLite;
- `app/services`: ingestão, parsing, chunking, retrieval, answer e auditoria;
- `app/infra/parsers`: implementação de leitura para `PDF`, `XLSX` e `CSV`;
- `app/infra/llm`: clientes da OpenAI para embeddings e resposta;
- `app/infra/vectorstore`: integração com ChromaDB;
- `app/schemas`: contratos de entrada e saída da API.

Essa separação deixa o pipeline de RAG entendível e auditável, sem depender de frameworks de orquestração como LangChain ou LlamaIndex.

## Fluxo de RAG

1. `POST /documents/upload` salva o arquivo e registra o documento.
2. O parser converte o arquivo em registros com metadados.
3. O chunking transforma o conteúdo em unidades recuperáveis.
4. Os chunks são persistidos no SQLite e indexados no ChromaDB.
5. `POST /queries/ask` gera embedding da pergunta e busca os chunks mais relevantes.
6. O serviço de resposta monta o contexto e força uma resposta baseada apenas na evidência recuperada.
7. O resultado final e os eventos relacionados ficam disponíveis na trilha de auditoria.

## Stack

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic v2
- SQLAlchemy
- SQLite
- PyMuPDF
- pandas
- openpyxl
- ChromaDB
- OpenAI API
- pytest
- Ruff
- Black
- Docker
- docker-compose

## Como rodar

### 1. Configuração

Para usar upload e query com a OpenAI, crie um `.env` a partir do `.env.example` e preencha `OPENAI_API_KEY`.

Variáveis principais:

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

### 2. Subir com Docker

```bash
docker-compose up --build
```

O `docker-compose.yml` já possui defaults para desenvolvimento local. Se existir um arquivo `.env`, o Docker Compose usa seus valores automaticamente.

### 3. Rodar localmente sem Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Check mínimo depois do bootstrap

Antes de fazer uma rodada maior de hardening, o fluxo básico precisa estar de pé:

1. `GET /health`
2. `POST /documents/upload`
3. `GET /documents`

Se quiser validar a pergunta ponta a ponta, configure uma `OPENAI_API_KEY` válida e teste também `POST /queries/ask`.

## Endpoints

- `GET /health`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /queries/ask`
- `GET /audit/queries`
- `GET /audit/queries/{query_id}`

## Exemplo de uso

### Health

```bash
curl http://localhost:8000/health
```

### Upload

```bash
curl -X POST http://localhost:8000/documents/upload ^
  -F "file=@docs/policies.csv"
```

### Listagem

```bash
curl http://localhost:8000/documents
```

### Pergunta

```bash
curl -X POST http://localhost:8000/queries/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What is the password policy?\",\"document_ids\":[],\"top_k\":5}"
```

## Testes e qualidade

Executar a suíte:

```bash
python -m pytest
```

Executar lint:

```bash
python -m ruff check .
python -m black --check .
```

## Limitações atuais

- não há autenticação nem isolamento por usuário;
- não há OCR para PDFs escaneados;
- a qualidade da resposta depende da evidência recuperada;
- não há reranker;
- não há processamento assíncrono para arquivos grandes.

## Roadmap

- filtros mais fortes por documento e tipo de fonte;
- melhores heurísticas de confiança;
- suporte a mais formatos corporativos;
- observabilidade mais rica para produção;
- autenticação e controle de acesso em uma próxima etapa.

## Por que este projeto demonstra AI Engineering

Este repositório mostra competências práticas de engenharia para sistemas com IA aplicada:

- pipeline de RAG manual e compreensível;
- integração real com embeddings, vetor store e LLM;
- recusa segura para reduzir hallucination;
- rastreabilidade via auditoria e citações;
- testes úteis em parser, chunking, upload e query flow;
- arquitetura simples o suficiente para manutenção e explicação em entrevista.

## Disclaimer

Este é um projeto de portfólio. Não envie documentos sensíveis de produção sem revisar governança, retenção, controle de acesso, política de logs e requisitos legais do seu ambiente.
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
