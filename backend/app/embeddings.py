from __future__ import annotations

import math
import os
from typing import Protocol

from fastapi import HTTPException
from openai import OpenAI, OpenAIError


class EmbeddingProvider(Protocol):
    model: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class OpenAIEmbeddingProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv('EMBEDDING_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.base_url = os.getenv('EMBEDDING_BASE_URL')
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail='OpenAI embeddings are selected but no EMBEDDING_API_KEY or OPENAI_API_KEY is configured.',
            )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = []
        try:
            client_options = {
                'api_key': self.api_key,
                'timeout': 30.0,
                'max_retries': 0,
            }
            if self.base_url:
                client_options['base_url'] = self.base_url
            with OpenAI(**client_options) as client:
                for offset in range(0, len(texts), 128):
                    response = client.embeddings.create(
                        model=self.model,
                        input=texts[offset:offset + 128],
                        encoding_format='float',
                    )
                    data = sorted(response.data, key=lambda item: item.index)
                    vectors.extend(list(item.embedding) for item in data)
        except OpenAIError as exc:
            raise HTTPException(
                status_code=503,
                detail='The embedding provider could not process this request. Check the embedding configuration and try again.',
            ) from exc

        if len(vectors) != len(texts):
            raise HTTPException(
                status_code=502,
                detail='The embedding provider returned an incomplete result.',
            )
        if any(
            not vector
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector)
            for vector in vectors
        ):
            raise HTTPException(
                status_code=502,
                detail='The embedding provider returned an invalid vector.',
            )
        return vectors


def get_embedding_provider() -> EmbeddingProvider | None:
    provider = os.getenv('EMBEDDING_PROVIDER', 'auto').strip().casefold()
    if provider in {'auto', 'openai'}:
        if provider == 'auto' and not (
            os.getenv('EMBEDDING_API_KEY') or os.getenv('OPENAI_API_KEY')
        ):
            return None
        return OpenAIEmbeddingProvider()
    if provider in {'tfidf', 'none'}:
        return None
    raise HTTPException(
        status_code=500,
        detail='Unsupported EMBEDDING_PROVIDER. Choose auto, openai, or tfidf.',
    )
