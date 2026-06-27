# CURRENT_TASK: Rich Model Management

## Objective
Redesign the Model Management system to support multiple LLM providers (Ollama, OpenAI, Anthropic, etc.) using a flexible, provider-agnostic configuration pattern.

## Background
The current implementation is a simple flat structure (Name, ID, Description) which only works for a single provider. To support a diverse ecosystem of local and cloud runtimes, the system needs a way to store provider-specific settings (API keys, base URLs, timeouts) without altering the database schema for every new provider.

## Functional Requirements
- **Provider Registry:** Support a list of predefined providers (Ollama, OpenAI, etc.).
- **Dynamic Configuration:** Store provider-specific settings in a JSON blob.
- **Model-Provider Link:** Each model must be associated with a specific provider.
- **Config Validation:** Validate that the provided configuration matches the requirements of the selected provider.
- **Health Check:** Ability to "ping" the provider to verify the model is reachable before saving.

## Non Functional Requirements
- **Extensibility:** Adding a new provider should only require adding a new adapter and a config schema.
- **Maintainability:** No database migrations should be required when adding new provider-specific settings.
- **Type Safety:** Use Pydantic for strict validation of the JSON configuration.

## Files Expected To Change
- `backend/src/database.py` (Update schema: add `providers` table, modify `models` table)
- `backend/src/schemas/__init__.py` (Add Pydantic models for Providers and ModelConfigs)
- `backend/src/routers/models.py` (Update CRUD endpoints to handle provider logic)
- `backend/src/services/ollama.py` (Update to align with new provider adapter pattern)

## Files That Must NOT Change
- `frontend/src/app/app.component.ts` (UI changes are deferred to a separate task)
- `backend/src/services/vector_stores.py` (Vector store logic is independent of model management)

## Acceptance Criteria
- [ ] `GET /api/providers` returns a list of supported runtimes and their required config fields.
- [ ] `POST /api/models` successfully saves a model with a valid JSON config for a specific provider.
- [ ] `POST /api/models` returns a 422 error if required config fields for the chosen provider are missing.
- [ ] `GET /api/models` returns the model along with its provider details.
- [ ] Database contains a `providers` table and the `models` table has a `provider_id` foreign key.

## Suggested Implementation Order
1. **Database Layer:** Create `providers` table and migrate `models` table to include `provider_id` and `config` (JSON).
2. **Schema Layer:** Define Pydantic models for `Provider`, `Model`, and provider-specific `Config` objects.
3. **Service Layer:** Implement a basic validation registry that maps `provider_type` to its corresponding Pydantic config schema.
4. **API Layer:** Update the `models` router to implement the new CRUD logic.

## Out Of Scope
- Angular UI implementation (this is a backend-only task).
- Implementing the actual LLM call logic (this task focuses on *management* and *configuration*).
- Authentication/API Key encryption.
