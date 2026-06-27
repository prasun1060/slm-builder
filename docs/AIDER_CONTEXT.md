# Aider Context

This repo is an MVP, not a finished product. Keep changes small and preserve the local-first workflow.

## Product Goal

Create an app that helps a user build a RAG-backed small language model experience from an existing LLM/runtime. The first runtime is Ollama and the first workflow is RAG, not fine-tuning.

## Current Flow

1. Create a model record for an Ollama model.
2. Create a pipeline and choose `chroma` or `mongodb`.
3. Add pasted text or upload `.txt`/`.md` files.
4. Index the documents into the chosen vector store.
5. Ask questions in the chat test panel.

## Implementation Rules

- Keep backend setup `uv`-based.
- Keep Chroma as the zero-config default.
- MongoDB must validate `uri`, `database`, `collection`, and `index_name`.
- Do not add auth, deployment, or fine-tuning until the RAG MVP is stable.
- Prefer improving the existing Angular standalone component before splitting into many files.

## Important Files

- `backend/main.py`
- `backend/src/database.py`
- `backend/src/schemas/__init__.py`
- `backend/src/routers/`
- `backend/src/services/`
- `frontend/src/app/app.component.ts`
- `frontend/src/app/app.component.html`
- `frontend/src/app/app.component.css`

## Plan

1. **Understand the Current Implementation**
   - Review the existing code in `backend/main.py`, `backend/app/database.py`, `backend/app/schemas/__init__.py`, `backend/app/routers/`, `backend/app/services/`, `frontend/src/app/app.component.ts`, `frontend/src/app/app.component.html`, `frontend/src/app/app.component.css`, and `docs/AIDER_CONTEXT.md`.
   - Identify the current flow and any areas that need improvement.

2. **Define the Goals**
   - Define the specific goals for the project, such as improving the user interface, adding new features, or fixing bugs.

3. **Create a Task List**
   - Create a list of tasks that need to be completed to achieve the goals. For example:
     - Improve the user interface
     - Add a new feature to allow users to upload files
     - Fix a bug in the backend

4. **Prioritize the Tasks**
   - Prioritize the tasks based on their importance and urgency. For example, prioritize tasks that will have the most significant impact on the user experience.

5. **Assign Responsibilities**
   - Assign responsibilities to team members based on their skills and expertise. For example, assign tasks related to the backend to a backend developer and tasks related to the frontend to a frontend developer.

6. **Set Deadlines**
   - Set deadlines for each task to ensure that the project is completed on time.

7. **Review and Adjust the Plan**
   - Review the plan regularly and adjust it as needed to ensure that the project is on track.
