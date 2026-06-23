# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Dependency management (use uv)
uv venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv pip install -e .                    # install production deps
uv pip install -e ".[dev]"            # install dev deps (pytest, ruff, mypy, etc.)

# Start services (see Makefile for individual service commands)
make up          # start Milvus Docker container
make start       # start all services (MCP + FastAPI)
make stop        # stop all services
make dev         # development mode with hot reload (foreground)
make restart     # restart all services and wait for readiness

# Code quality
make format      # ruff format + isort fix
make lint        # ruff check
make fix         # auto-fix lint issues
make type-check  # mypy type checking
make security    # bandit security scan
make check-all   # format + lint + test (full CI pipeline)

# Testing
make test        # pytest with coverage (uses --cov=app)
make test-quick  # pytest without coverage (faster)
# Run a single test file:
pytest tests/test_something.py -v
# Run a single test function:
pytest tests/test_something.py::test_function_name -v

# Pre-commit
make pre-commit-install   # install git hooks (format, lint, security, docformatter)
make pre-commit           # run all hooks manually

# Docs / documents
make upload               # upload all markdown files from pm-docs/ to vector DB
make docs                 # open API docs at http://localhost:9900/docs

# Utilities
make logs                 # tail FastAPI server logs
make clean                # remove caches, build artifacts, PID files
make status               # check Docker container status
make status-mcp           # check MCP service status
```

On **Windows** (no `make`): use `.\start-windows.bat` / `.\stop-windows.bat` or follow the manual steps in README.md.

## Architecture Overview

This is **PM AI Agent** — a FastAPI app providing RAG-powered Q&A and intelligent project management. It uses LangChain/LangGraph, Milvus vector DB, and MCP (Model Context Protocol) servers for tool integration.

### High-Level Data Flow

```
Browser (static/) → FastAPI (app/main.py)
  ├─ /api/chat(_stream)   → RagAgentService  → LLM + tools (knowledge, MCP)
  ├─ /api/pm              → PMService         → Plan-Execute (LangGraph)
  ├─ /api/upload          → DocumentSplitter  → VectorEmbedding → Milvus
  └─ /api/health          → Milvus health check
```

### Two Main Pipelines

**1. RAG Q&A Pipeline** (`app/services/rag_agent_service.py`):
LangGraph agent with checkpointer (MemorySaver) for multi-turn conversation. Tools include `retrieve_knowledge` (Milvus vector search), `get_current_time`, and MCP tools. Session state persists via thread_id in MemorySaver.

**2. PM Agent Pipeline** (`app/services/pm_service.py`):
Implements the Plan-Execute pattern via LangGraph `StateGraph` for project management tasks:
- **Planner** (`app/agent/pm/planner.py`): Queries knowledge base for relevant project context, then uses LLM with structured output to generate a step-by-step plan.
- **Executor** (`app/agent/pm/executor.py`): Executes each step in the plan using MCP tools and LLM.
- **Replanner** (`app/agent/pm/replanner.py`): Evaluates progress and decides `continue` / `replan` / `respond`.

State flows: `planner → executor → replanner → executor... → END`.

### LLM Factory Pattern

`app/core/llm_factory.py` provides a single `LLMFactory.create_chat_model()` that returns a `langchain_openai.ChatOpenAI` instance configured for OpenAI-compatible APIs. All agent code calls `llm_factory.create_chat_model()` rather than instantiating LLMs directly — to change providers, update LLMFactory.

### Vector Store Architecture

- Single Milvus collection **`biz`** with 1024-dim vectors, IVF_FLAT index (L2 metric).
- `MilvusClientManager` (`app/core/milvus_client.py`) manages low-level connection, collection creation, schema/health checks, and a critical monkey-patch to fix pymilvus ORM alias conflicts (`_patch_pymilvus_milvus_client_orm_alias`).
- `VectorStoreManager` (`app/services/vector_store_manager.py`) wraps LangChain's `Milvus` vector store, handles document add/delete/search.
- `DashScopeEmbeddings` (`app/services/vector_embedding_service.py`) implements LangChain's `Embeddings` interface but supports **both standard OpenAI API and MiniMax embedding API** with automatic endpoint detection. The global instance is configured to use **SiliconFlow** (`Qwen/Qwen3-Embedding-8B`) as primary, falling back to DashScope only if SiliconFlow key is absent.
- Documents from `pm-docs/` are uploaded via the `/api/upload` endpoint, split by `DocumentSplitterService`, embedded, and stored in Milvus.

### MCP Integration

Two MCP servers (`mcp_servers/`) provide tools consumed by the agents:

| Server | Port | Tools |
|--------|------|-------|
| `project_server.py` | 8003 | Project info, tasks, milestones, risk management |
| `knowledge_server.py` | 8004 | Knowledge base search, meeting notes, documents |

MCP clients are managed as singletons via `app/agent/mcp_client.py` using `langchain_mcp_adapters.MultiServerMCPClient`. All MCP tool calls have an automatic retry interceptor (3 attempts with exponential backoff). Server config comes from `.env` (`MCP_PROJECT_URL`, `MCP_KNOWLEDGE_URL`).

**MCP servers currently return mock data** — production integration requires real API credentials.

### Configuration

All config via `pydantic-settings` in `app/config.py`, loaded from `.env`. Global `config` singleton used throughout. Key settings:

- `DASHSCOPE_*` — LLM API credentials (OpenAI-compatible, supports DeepSeek/MiniMax/DashScope)
- `SILICONFLOW_*` — Embedding API credentials (SiliconFlow as primary provider)
- `MILVUS_*` — Milvus host/port
- `RAG_TOP_K` — number of documents retrieved per query
- `CHUNK_MAX_SIZE` / `CHUNK_OVERLAP` — document splitting parameters
- `MCP_PROJECT_URL` / `MCP_KNOWLEDGE_URL` — MCP server endpoints

### Static Frontend

The web UI is vanilla HTML/CSS/JS in `static/` — no build step, served directly by FastAPI at `/`.

### Logging

Loguru configured in `app/utils/logger.py` (auto-loaded on app import). Console output (colored, DEBUG level in dev) + daily file rotation (`logs/app_YYYY-MM-DD.log`, retained 7 days, compressed). MCP servers and FastAPI each write to separate log files (`server.log`, `mcp_knowledge.log`, `mcp_project.log`).

### Testing

Pytest is configured in `pyproject.toml` (with coverage, asyncio_mode=auto) but **a `tests/` directory does not yet exist**.

### Key Dependencies

- `fastapi` + `uvicorn` — web framework
- `langchain` + `langchain-openai` + `langgraph` — agent framework
- `pymilvus` + `langchain-milvus` — vector store
- `langchain-mcp-adapters` + `fastmcp` — MCP integration
- `loguru` — logging
- `pydantic` + `pydantic-settings` — data models & config
