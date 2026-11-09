from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


QuestionType = Literal[
    'multiple_choice',
    'true_false',
    'short_answer',
    'essay',
    'scenario_based',
    'case_study',
    'application',
]
Difficulty = Literal['easy', 'intermediate', 'hard']


class GeneratedQuestion(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    difficulty: Difficulty
    options: list[str] | None = None
    correct_answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


def validate_question_batch(
    questions: list[dict],
    source_context: str,
    semantic_similarities: list[float] | None = None,
) -> list[dict]:
    validated = []
    seen: list[set[str]] = []
    source_tokens = _tokens(source_context)

    for index, raw_question in enumerate(questions):
        try:
            question = GeneratedQuestion.model_validate(raw_question)
        except ValidationError as exc:
            raise ValueError('Generated question did not match the required schema.') from exc

        if question.question_type == 'multiple_choice':
            options = question.options or []
            if (
                len(options) < 2
                or any(not option.strip() for option in options)
                or question.correct_answer not in options
            ):
                raise ValueError('Generated multiple-choice question has invalid options or answer.')
        elif question.question_type == 'true_false':
            if question.options != ['True', 'False'] or question.correct_answer not in question.options:
                raise ValueError('Generated true-or-false question has invalid options or answer.')

        question_tokens = _tokens(question.question_text)
        duplicate_index = next(
            (
                previous_index
                for previous_index, previous_tokens in enumerate(seen)
                if _similarity(question_tokens, previous_tokens) >= 0.85
            ),
            None,
        )
        seen.append(question_tokens)

        answer_tokens = _tokens(question.correct_answer)
        overlap = (
            len((question_tokens | answer_tokens) & source_tokens)
            / max(1, len(question_tokens | answer_tokens))
            if source_tokens else None
        )
        semantic_similarity = (
            semantic_similarities[index]
            if semantic_similarities and index < len(semantic_similarities)
            else None
        )
        validated.append({
            **question.model_dump(),
            'quality_review': {
                'status': 'regeneration_required' if duplicate_index is not None else 'needs_review',
                'duplicate_of_question': duplicate_index + 1 if duplicate_index is not None else None,
                'source_support': (
                    'semantic_similarity_screen' if semantic_similarity is not None
                    else 'not_assessed' if overlap is None
                    else 'low_lexical_overlap' if overlap < 0.1
                    else 'lexical_overlap_found'
                ),
                'source_overlap': round(overlap, 3) if overlap is not None else None,
                'semantic_similarity': (
                    round(semantic_similarity, 3)
                    if semantic_similarity is not None else None
                ),
                'review_note': (
                    'Embedding similarity is only a relevance screening signal, not proof of support; human review is required.'
                    if semantic_similarity is not None
                    else 'Lexical overlap is only a screening signal; human review is required.'
                    if overlap is not None
                    else 'No retrieved source context was available for source-support screening.'
                ),
            },
        })

    return validated


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r'[a-z0-9]+', text.casefold())
        if len(token) > 2
    }


def _similarity(first: set[str], second: set[str]) -> float:
    if not first or not second:
        return 0.0
    return len(first & second) / len(first | second)
