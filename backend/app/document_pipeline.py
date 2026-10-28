from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import fitz


class DocumentProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


def extract_pdf_pages(content: bytes) -> list[ExtractedPage]:
    try:
        with fitz.open(stream=content, filetype='pdf') as pdf:
            if pdf.is_encrypted:
                raise DocumentProcessingError('Password-protected PDFs are not supported.')
            pages = [
                ExtractedPage(page_number=index + 1, text=page.get_text('text').strip())
                for index, page in enumerate(pdf)
            ]
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise DocumentProcessingError('The uploaded file is not a readable PDF.') from exc

    if not any(page.text for page in pages):
        raise DocumentProcessingError(
            'No selectable text was found in the PDF. Scanned documents require OCR and are not supported yet.'
        )
    return pages


def split_pages(
    pages: Iterable[ExtractedPage],
    max_words: int = 350,
    overlap_words: int = 50,
) -> list[ExtractedPage]:
    if max_words <= 0 or overlap_words < 0 or overlap_words >= max_words:
        raise ValueError('Chunk sizes must be positive and overlap must be smaller than the chunk size.')

    chunks = []
    step = max_words - overlap_words
    for page in pages:
        words = page.text.split()
        for offset in range(0, len(words), step):
            text = ' '.join(words[offset:offset + max_words]).strip()
            if text:
                chunks.append(ExtractedPage(page_number=page.page_number, text=text))
    return chunks


def retrieve_relevant_chunks(
    query: str,
    chunks: Iterable[tuple[str, int]],
    limit: int = 4,
) -> list[tuple[str, int]]:
    documents = list(chunks)
    if not documents or limit <= 0:
        return []

    tokenized = [_tokenize(text) for text, _ in documents]
    query_tokens = _tokenize(query)
    if not query_tokens:
        return documents[:limit]

    document_frequency = Counter(
        token
        for tokens in tokenized
        for token in set(tokens)
    )
    total_documents = len(tokenized)

    def vectorize(tokens: list[str]) -> dict[str, float]:
        frequencies = Counter(tokens)
        vector = {
            token: (1 + math.log(count))
            * (math.log((total_documents + 1) / (document_frequency[token] + 1)) + 1)
            for token, count in frequencies.items()
        }
        magnitude = math.sqrt(sum(weight * weight for weight in vector.values()))
        return {token: weight / magnitude for token, weight in vector.items()} if magnitude else {}

    query_vector = vectorize(query_tokens)
    ranked = []
    for index, tokens in enumerate(tokenized):
        vector = vectorize(tokens)
        score = sum(weight * vector.get(token, 0.0) for token, weight in query_vector.items())
        if score > 0:
            ranked.append((score, index))

    if not ranked:
        return documents[:limit]
    ranked.sort(key=lambda result: result[0], reverse=True)
    return [documents[index] for _, index in ranked[:limit]]


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) > 1
    ]
