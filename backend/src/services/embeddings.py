"""Small deterministic embedding service for local MVP indexing."""

from __future__ import annotations

import hashlib
import math
import re


class HashEmbeddingService:
    """Embeds text without a remote model so the MVP works offline."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        length = math.sqrt(sum(value * value for value in vector))
        if not length:
            return vector
        return [value / length for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


embedding_service = HashEmbeddingService()
