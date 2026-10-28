from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class GoogleLogin(BaseModel):
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: Dict[str, Any]


class DocumentUpload(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=20, max_length=600000)
    filename: str | None = None


class QuizGenerate(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    question_type: Literal[
        'multiple_choice',
        'true_false',
        'short_answer',
        'essay',
        'scenario_based',
        'case_study',
        'application',
        'mixed',
    ] = 'multiple_choice'
    difficulty: Literal['easy', 'intermediate', 'hard'] = 'intermediate'
    count: int = Field(default=3, ge=1, le=8)
    document_id: str | None = None
    source_text: str | None = Field(default=None, max_length=600000)


class AssessmentAnswer(BaseModel):
    question_id: str
    answer: str


class AssessmentSubmit(BaseModel):
    quiz_id: str
    answers: List[AssessmentAnswer]


class StudyGenerate(BaseModel):
    kind: Literal['summary', 'flashcards', 'concepts', 'revision_notes', 'definitions']
    topic: str = Field(..., min_length=2, max_length=200)
    source_text: str | None = Field(default=None, max_length=600000)
    document_id: str | None = None


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    provider: str
    is_verified: bool
    avatar_url: str | None = None
    created_at: str
    last_login: str

    model_config = ConfigDict(from_attributes=True)
