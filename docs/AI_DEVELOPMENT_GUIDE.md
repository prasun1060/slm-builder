# AI Development Guide: SLM Builder

This guide provides the necessary constraints and standards for AI agents contributing to the SLM Builder codebase. Follow these rules strictly to maintain architectural integrity and minimize technical debt.

## 1. Project Philosophy
- **Local-First:** Prioritize local LLM runtimes and vector stores.
- **Provider Agnostic:** The core logic must never depend on a specific provider's SDK.
- **Developer-Centric:** Build for developers who need transparency (citations, logs, tuning).
- **Modular:** Every feature should be a pluggable component.

## 2. Architecture Principles
- **Clean Architecture:** 
    - `Routers` $\rightarrow$ `Services` $\rightarrow$ `Adapters` $\rightarrow$ `External APIs`.
- **No Provider Leakage:** Provider-specific types (e.g., `chromadb.Collection`) must stay inside the Adapter layer. Services must use generic Pydantic schemas or ABCs.
- **Async-First:** All long-running operations (indexing, large LLM calls) must be handled as background tasks.
- **State-Driven:** Use explicit status fields (`PENDING`, `INDEXED`, `FAILED`) for data processing.

## 3. Folder Responsibilities
- `backend`: Folder where all backend code sits
- `backend/src/routers/`: HTTP endpoints, request/response validation.
- `backend/src/services/`: Business logic and orchestration.
- `backend/src/adapters/`: Translation between generic interfaces and provider SDKs.
- `backend/src/schemas/`: Pydantic models for API and internal data transfer.
- `backend/src/database.py`: SQLAlchemy models and session management.
- `frontend`: Folder where all frontend code sits
- `frontend/src/app/components/`: Small, reusable UI units.
- `frontend/src/app/services/`: API communication and state management.

## 4. Coding Standards & Naming
- **Python:** 
    - Use type hints for all function signatures.
    - Follow PEP 8.
    - Use `snake_case` for functions/variables, `PascalCase` for classes.
- **TypeScript/Angular:**
    - Use strict typing; avoid `any`.
    - Follow Angular Style Guide (standalone components).
    - Use `camelCase` for variables/functions, `PascalCase` for classes.
- **Naming:**
    - Interfaces: `I` prefix (e.g., `IVectorStore`).
    - Adapters: `[Provider]Adapter` (e.g., `OllamaAdapter`).

## 5. Dependency & API Rules
- **Backend Dependencies:** Managed via `uv`. Use `pyproject.toml` as the source of truth.
- **API Conventions:**
    - RESTful paths: `/api/resource` (plural).
    - Standard HTTP codes: `201 Created`, `202 Accepted` (for async), `422 Unprocessable Entity` (validation).
    - All responses must be wrapped in a consistent JSON structure.
- **Database Conventions:**
    - Use SQLite for metadata.
    - Use JSON columns for provider-specific configurations to avoid schema migrations.
    - Always use SQLAlchemy ORM; avoid raw SQL.

## 6. Angular Conventions
- **Standalone Components:** No `NgModule`. Use `imports: [...]` within the component decorator.
- **Service-Based State:** Do not store business state in components; use injectable services.
- **Dynamic Forms:** Use the `config_schema` from the backend to render provider-specific fields.

## 7. AI Agent Workflow
- **Context Management:** Read `docs/ARCHITECTURE.md` and `docs/BACKLOG.md` before starting any task.
- **Atomic Changes:** Modify only the files necessary for the current task.
- **Verification:** Always verify that changes do not break the `IVectorStore` or `ILLMProvider` abstractions.
- **Documentation:** Update `docs/BACKLOG.md` when a task is completed.
