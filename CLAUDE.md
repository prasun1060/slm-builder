# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ✨ Project Goal
The primary objective of the SLM Builder is to create a sophisticated platform that allows users, regardless of their technical knowledge, to build complex Retrieval-Augmented Generation (RAG) pipelines visually using a **drag-and-drop UI**. This system must enable seamless integration with diverse models and databases.

## 🧠 High-Level Architecture & Overview

The SLM Builder project consists of two distinct but interconnected components: a **Python Backend** and an **Angular Frontend**. Communication is handled via RESTful APIs, typically exposed through the backend's routing system.

### 📁 Backend (Python)
*   **Purpose**: Core business logic, LLM orchestration, data persistence, and API exposure. The primary goal is to manage the lifecycle of SLMs and execute complex AI pipelines. This layer must evolve to receive and process dynamic workflow definitions from the frontend UI.
*   **Structure**: Organized within `backend/src/`.
    *   `routers/*`: Contains the API endpoints (`rag.py`, `models.py`, etc.). These act as controllers, taking HTTP requests and delegating logic to the service layer. They must be updated to handle a *workflow graph definition* instead of just single RAG queries.
    *   `services/*`: This is the heart of the application's intelligence. It contains reusable modules for specific tasks:
        *   `ollama.py`: Handles communication with local or remote LLM endpoints (e.g., Ollama).
        *   `vector_stores.py`: Manages interactions with vector databases, crucial for RAG. Must abstract the database connection details based on user input/workflow definition.
        *   `rag_orchestrator.py`: Contains the complex logic for stitching together retrieval steps (fetching documents) and generation steps (calling the LLM). This is the primary target for refactoring to support graph traversal of custom pipelines.
    *   `schemas/`: Utilizes Pydantic models (`schemas.py`) for defining strict data types, validating incoming requests, and structuring outgoing responses, ensuring API contract reliability for both single calls and complex workflow payloads.

### 🖼️ Frontend (Angular)
*   **Purpose**: The user interface for interacting with SLMs, managing model lists, and visualizing complex pipelines. This component requires a significant overhaul to support a true visual graph editor (drag-and-drop canvas).
*   **Structure**: Located in `frontend/src/`.
    *   `app.component.*`: Main application shell and routing setup (`app.routes.ts`).
    *   Components (`components/*`): Self-contained UI units (e.g., `chat-playground`, `model-list`) that handle specific views. A new component, perhaps called `workflow-builder`, will be required here.
    *   `api.service.ts`: The single point of truth for all backend API calls, managing HTTP requests and error handling across the application. It must now submit serialized workflow definitions to the backend.

### 🌐 Data Flow: RAG Pipeline Example (Current)
1.  **User Interaction**: Frontend component triggers an action (e.g., asking a question in the chat playground).
2.  **API Call**: `api.service.ts` sends the request to the Backend API router (`backend/src/routers/rag.py`).
3.  **Orchestration**: The backend calls `services/rag_orchestrator.py`.
4.  **Retrieval**: The orchestrator uses `services/vector_stores.py` to query a vector database with the user's input, retrieving relevant context documents.
5.  **Generation**: These retrieved documents and the original query are passed to the LLM client (`ollama.py`) for final generation.
6.  **Response**: The generated response is returned through the router back to `api.service.ts` and finally displayed in the frontend component.

### 🛠️ Development Commands

Since no specific setup scripts (like a top-level `package.json` or Makefile) were visible, these are common commands for this stack assuming standard tooling installation (`npm install`, `pip install -r requirements.txt`).

### ⚙️ Setup & Dependencies
1.  **Backend Setup**: Install Python dependencies into the virtual environment:
    ```bash
    # Assumes venv activation is done
    pip install -r backend/requirements.txt # (Use actual path)
    ```
2.  **Frontend Setup**: Navigate to the frontend directory and install Node dependencies:
    ```bash
    cd frontend
    npm install
    cd .. # Back to root
    ```

### ▶️ Running & Testing
1.  **Run Backend Server**: Start the FastAPI/Python server (assuming `slm_builder_backend` is the entry point):
    ```bash
    # Replace 'uvicorn' or 'python -m uvicorn' with actual runner if different
    uvicorn backend.src.slm_builder_backend:app --reload
    ```
2.  **Run Frontend (Angular)**: Serve the Angular application in a development server, which typically proxies API requests to the running backend.
    ```bash
    ng serve --proxy-mappings backend:http://localhost:8000
    ```
3.  **Running All Services**: For full local development, run both services concurrently (e.g., using `concurrently` or separate terminals).

### ✅ Testing Workflow
*   **General Backend Test**: Run all unit and integration tests for the backend logic:
    ```bash
    pytest backend/tests/
    ```
*   **Single Unit Test**: To test a specific module, use the pytest command targeting that file (e.g., testing RAG orchestration):
    ```bash
    pytest backend/src/services/rag_orchestrator.py::test_rag_flow
    ```

## 🧹 Linting & Formatting
*   **Backend**: Run Python linter/formatter:
    ```bash
    ruff check backend/src --fix  # Or black / flake8 as appropriate
    ```
*   **Frontend**: Run Angular linting:
    ```bash
    ng lint
    ```