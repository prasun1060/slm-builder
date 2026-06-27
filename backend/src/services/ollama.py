"""Ollama HTTP client helpers."""

from __future__ import annotations

import os

import httpx


class OllamaUnavailableError(RuntimeError):
    pass


async def generate_answer(model_id: str, question: str, context: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    prompt = (
        "Answer the question using only the context below. "
        "If the context does not contain the answer, say you do not know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )
    payload = {"model": model_id, "prompt": prompt, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{base_url}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(str(exc)) from exc

    data = response.json()
    return data.get("response", "").strip() or "I do not know."
