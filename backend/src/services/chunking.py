"""Document chunking helpers."""

from __future__ import annotations

from ..schemas.schemas import Chunk


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[Chunk]:
    clean_text = " ".join(text.split())
    if not clean_text:
        return []

    chunk_size = max(chunk_size, 100)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))
    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []

    for index, start in enumerate(range(0, len(clean_text), step)):
        piece = clean_text[start : start + chunk_size].strip()
        if piece:
            chunks.append(Chunk(text=piece, index=index))
        if start + chunk_size >= len(clean_text):
            break

    return chunks
